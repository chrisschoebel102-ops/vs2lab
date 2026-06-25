import random
import logging

# coordinator messages
from const2PC import PEER_STATE, PREPARE_COMMIT, READY_COMMIT, VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT
# participant decissions
from const2PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const2PC import VOTE_COMMIT, VOTE_ABORT, NEED_DECISION
# misc constants
from const2PC import TIMEOUT

import stablelog


class Participant:
    """
    Implements a two phase commit participant.
    - state written to stable log (but recovery is not considered)
    - in case of coordinator crash, participants mutually synchronize states
    - system blocks if all participants vote commit and coordinator crashes
    - allows for partially synchronous behavior with fail-noisy crashes
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log(
            "participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.2pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state = 'NEW'

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_ABORT if random.random() > 2/3 else LOCAL_SUCCESS

    def _enter_state(self, state):
        self.stable_log.info(state)  # Write to recoverable persistant log file
        self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def _elect_coordinator(self):
        new_coord_id = min(self.all_participants)
        return new_coord_id == self.participant  
    
    def _run_as_new_coordinator(self):
        """
        P_k übernimmt Koordinator-Rolle laut Spezifikation:
        1. Sendet eigenen Zustand an alle
        2. Wartet auf Antworten
        3. Entscheidet basierend auf eigenem Zustand
        """
        others = {p for p in self.all_participants if p != self.participant}
        print("Participant {} becomes new coordinator in state {}.".format(
            self.participant, self.state))

        # Schritt 1: Eigenen Zustand an alle senden
        self.channel.send_to(others, (PEER_STATE, self.state))

        # Schritt 2: Auf Antworten warten
        # (andere Participants schicken ihren Zustand zurück)
        yet_to_receive = list(others)
        peer_states = {}
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(others, TIMEOUT * 3)
            if not msg:
                break  # Timeout - mit den bisherigen Infos weiterarbeiten
            sender, content = msg[0], msg[1]
            if isinstance(content, tuple) and content[0] == PEER_STATE:
                peer_states[sender] = content[1]
                if sender in yet_to_receive:
                    yet_to_receive.remove(sender)

        # Schritt 3: Entscheidung basierend auf eigenem Zustand
        if self.state == 'READY':
            # Fall 1: P_k war READY → GLOBAL_ABORT
            self._enter_state('ABORT')
            self.channel.send_to(others, GLOBAL_ABORT)
            return GLOBAL_ABORT

        elif self.state == 'PRECOMMIT':
            # Fall 2: P_k war PRECOMMIT → GLOBAL_COMMIT
            self._enter_state('COMMIT')
            self.channel.send_to(others, GLOBAL_COMMIT)
            return GLOBAL_COMMIT

        else:
            # Fall 3: P_k war ABORT oder COMMIT → alle folgen
            self.channel.send_to(others, GLOBAL_ABORT if self.state == 'ABORT' else GLOBAL_COMMIT)
            return GLOBAL_ABORT if self.state == 'ABORT' else GLOBAL_COMMIT

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')  # Start in local INIT state.

    def run(self):
        decision = LOCAL_ABORT  # Default decision is to locally abort if anything goes wrong
        # Wait for start of joint commit
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:  # Crashed coordinator - give up entirely
            # decide to locally abort (before doing anything)
            self._enter_state('ABORT')

        else:  # Coordinator requested to vote, joint commit starts
            assert msg[1] == VOTE_REQUEST
            # Firstly, come to a local decision
            decision = self._do_work()  # proceed with local activities

            # If local decision is negative,
            # then vote for abort and quit directly
            if decision == LOCAL_ABORT:
                self.channel.send_to(self.coordinator, VOTE_ABORT)
                self._enter_state('ABORT')

            # If local decision is positive,
            # we are ready to proceed the joint commit
            else:
                assert decision == LOCAL_SUCCESS
                self._enter_state('READY')

                # Notify coordinator about local commit vote
                self.channel.send_to(self.coordinator, VOTE_COMMIT)

                # Wait for coordinator to notify the final outcome
                msg = self.channel.receive_from(self.coordinator, TIMEOUT)

                if not msg:  # Crashed coordinator
                    if self._elect_coordinator():
                        decision = self._run_as_new_coordinator()
                    else:
                        # Auf PEER_STATE vom neuen Coordinator warten
                        msg = self.channel.receive_from(self.all_participants, TIMEOUT * 3)
                        if msg and isinstance(msg[1], tuple) and msg[1][0] == PEER_STATE:
                            # Eigenen Zustand zurückschicken
                            self.channel.send_to({msg[0]}, (PEER_STATE, self.state))
                            # Auf finale Entscheidung warten
                            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 3)
                            decision = msg[1] if msg and msg[1] in [GLOBAL_COMMIT, GLOBAL_ABORT] else GLOBAL_ABORT
                        else:
                            decision = GLOBAL_ABORT
                        self._enter_state('COMMIT' if decision == GLOBAL_COMMIT else 'ABORT')

                else:  # Coordinator came to a decision
                    decision = msg[1]

                    if decision == PREPARE_COMMIT:
                        self._enter_state('PRECOMMIT')
                        self.channel.send_to(self.coordinator, READY_COMMIT)

                        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

                    if not msg:  # Crashed coordinator
                        if self._elect_coordinator():
                            decision = self._run_as_new_coordinator()
                        else:
                            # Auf PEER_STATE vom neuen Coordinator warten
                            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 3)
                            if msg and isinstance(msg[1], tuple) and msg[1][0] == PEER_STATE:
                                # Eigenen Zustand zurückschicken
                                self.channel.send_to({msg[0]}, (PEER_STATE, self.state))
                                # Auf finale Entscheidung warten
                                msg = self.channel.receive_from(self.all_participants, TIMEOUT * 3)
                                decision = msg[1] if msg and msg[1] in [GLOBAL_COMMIT, GLOBAL_ABORT] else GLOBAL_ABORT
                            else:
                                decision = GLOBAL_ABORT
                            self._enter_state('COMMIT' if decision == GLOBAL_COMMIT else 'ABORT')

                    else:  # Coordinator came to a decision
                        decision = msg[1]
                    if decision == GLOBAL_COMMIT:
                        self._enter_state('COMMIT')
                    else:
                        assert decision in [GLOBAL_ABORT, LOCAL_ABORT]
                        self._enter_state('ABORT')

        # Help any other participant when coordinator crashed
        num_of_others = len(self.all_participants) - 1
        while num_of_others > 0:
            num_of_others -= 1
            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 2)
            if msg and msg[1] == NEED_DECISION:
                self.channel.send_to({msg[0]}, decision)

        return "Participant {} terminated in state {} due to {}.".format(
            self.participant, self.state, decision)
