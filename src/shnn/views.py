from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage, MTurkPage
from .models import Constants
import numpy as np
import time, random, math
from datetime import datetime
from otree_mturk_utils.views import CustomMturkPage, CustomMturkWaitPage, CustomWaitPageTreatment, SetTimeWaitPage
from otree.models import Participant
from django.http import HttpResponseRedirect, Http404, HttpResponse


'''
Because the Introduction is "Page 1", most pages are set back by an index of + 1
Order:
        1: Introduction,
        2: StartShuffleWaitPage,
        2: Question1,
        3: WaitPage,
        3: Question2,
           ...
        N: ResultsWaitPage,
        N: Results
'''


class Introduction(Page):
    timer_text = 'You must agree before the timer expires or you will not be able to participate:'

    form_model = models.Player
    form_fields = ['proceed_confirmation']


    def is_displayed(self):
        if self.round_number == 1:
            self.player.timestamp_begin = self.player.participant.vars['round_start_time'] = time.time()
            self.session.vars['show_pages_after_results'] = True
            #self.session.vars['block_overwrite'] = False
        return self.round_number == 1

    # Time to display on custom wait page
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the time until the experiment begins
        time_left = self.get_timeout_seconds()

        # Set to zero if time is negative
        if str(time_left)[0] == "-": time_left = 0

        context.update({
            'time_left': round(time_left),
        })
        return context

    def before_next_page(self):

        if self.round_number == 1:
            # Save to persistent variable to determine active vs inactive
            if self.player.proceed_confirmation == 1:
                self.participant.vars['proceed_confirmation'] = self.player.proceed_confirmation
            else:
                self.participant.vars['proceed_confirmation'] = False
            self.player.time_to_answer = time.time() - self.player.participant.vars['round_start_time']

    def get_timeout_seconds(self):
        return Constants.time_to_begin.timestamp() - time.time()

    timeout_seconds = get_timeout_seconds



# Participants are shuffled in this wait page
class StartShuffleWaitPage(SetTimeWaitPage):#CustomWaitPageTreatment):

    # template_name = 'shnn/WaitPageTreatment.html'
    body_text = "Thank you for waiting while other players make their selections."
    wait_for_all_groups = True

    time_to_begin = Constants.time_to_begin

    # Time to display on custom wait page
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the time until the experiment begins
        time_left = self.get_timeout_seconds()

        # Set to zero if time is negative
        if str(time_left)[0] == "-": time_left = 0

        context.update({
            'time_left': round(time_left),
        })
        return context

    def get_timeout_seconds(self):
        return Constants.time_to_begin.timestamp()- time.time()

    timeout_seconds = get_timeout_seconds

    # These are defaults from the custom wait page plugin for otree
    #timeout_seconds = time_to_begin #60
    pay_by_time = 0 #0.12
    startwp_timer = 60
    use_task = False

    # round to randomize
    randomization_round = Constants.randomization_round + 1 # Introduction is R1

    def after_all_players_arrive(self):

        # in second round, randomize the questions
        if self.round_number == self.randomization_round:

            # Separate players that have clicked the accept button and consider them active
            active, inactive = [], []
            for p in self.subsession.get_players():
                if ('proceed_confirmation' in p.participant.vars) and (p.participant.vars['proceed_confirmation'] == True):
                    active.append(p)
                else:
                    inactive.append(p)

            # Try to fill treatment layers with all active players
            self.session.vars['active_layers'] = (len(active) // Constants.players_per_group) #- Constants.baseline_layers

            # Randomize both groups and concatenate
            random.shuffle(active)
            random.shuffle(inactive)
            sorted_players = active + inactive

            # Put players into groups, keeping active players together
            group_matrix = []
            ppg = Constants.players_per_group
            for i in range(0, len(sorted_players), ppg):
                group_matrix.append(sorted_players[i:i+ppg])

            # set new groups
            self.subsession.set_group_matrix(group_matrix)
            m = self.subsession.get_group_matrix()
            matrix = self.subsession.assign_control_questions(m)

            # Set session expiry time as beginning of experiment
            expiry = Constants.time_to_begin.timestamp()
            self.session.vars['expiry'] = expiry

            for p in self.subsession.get_players():
                p.timestamp_begin = p.participant.vars['round_start_time'] = time.time()

    # Only display this page in the round where we want to randomize
    def is_displayed(self):
        if self.round_number == self.randomization_round:

            # Advance players when timeout_seconds hits 0
            if self.timeout_seconds() <= 0:

                # Get the maximum page index and round number from all participants
                max_index, max_round_number = 0, 0
                for p in self.subsession.get_players():
                    if p.participant._index_in_pages > max_index:
                        max_index = p.participant._index_in_pages
                    if (p.participant._round_number is not None) and (p.participant._round_number > max_round_number):
                        max_round_number = p.participant._round_number

                # Set the index and page number for participants that are behind when the timer expires
                for p in self.subsession.get_players():
                    # Players that haven't started yet will have round_number of "None"
                    if p.participant._round_number is None:
                        p.participant._round_number = max_round_number
                        p.participant._index_in_pages = max_index

                    # Players that are behind current max round and index
                    elif (p.participant._round_number != max_round_number) or (p.participant._index_in_pages != max_index):
                        p.participant._round_number = max_round_number
                        p.participant._index_in_pages = max_index

        return self.round_number == self.randomization_round

    def vars_for_template(self):
        v =  {
            'timeout_seconds': str(self.timeout_seconds),
            'waiting_bonus': str(self.pay_by_time),
                }
        return v

# Participants are NOT shuffled in this wait page
class WaitPage(CustomWaitPageTreatment):
    body_text = "Thank you for waiting while other players make their selections."
    wait_for_all_groups = True

    # Don't show this page in the round where we want to randomize
    def is_displayed(self):

        if (self.round_number > 2) and (self.round_number <= self.session.vars['active_layers'] + 1):

            # Get the maximum page index and round number from all participants
            if self.timeout_seconds() <= 0:

                max_index, max_round_number = 0, 0

                # Set the index and page number for participants that are behind when the timer expires
                for p in self.subsession.get_players():
                    if p.participant._index_in_pages > max_index:
                        max_index = p.participant._index_in_pages
                    if p.participant._round_number > max_round_number:
                        max_round_number = p.participant._round_number



                # Players that are behind current max round and index
                for p in self.subsession.get_players():
                    if (p.participant._round_number != max_round_number) or (p.participant._index_in_pages != max_index):
                        p.participant._round_number = max_round_number
                        p.participant._index_in_pages = max_index

        return (self.round_number > 2) and (self.round_number <= self.session.vars['active_layers'] + 1)

    def after_all_players_arrive(self):
        # set N to be the round where treament begins where (round_number > N)
        t_round_n = 2

        if (self.round_number > t_round_n) and (self.round_number <= self.session.vars['active_layers'] + 1):
            # to set block later
            layer = self.session.vars['active_layers'] + 1

            # Keep groups the same after they are randomized
            self.subsession.group_like_round(t_round_n)
            matrix = self.subsession.get_group_matrix()

            # For some reason otree is replaying the last round in the
            # background when it should be going to the Results Page
            # This prevents it from shuffling questions and overwriting the prev round
            if 'block_overwrite' in self.session.vars:
                question_ids = self.subsession.set_prev_questions(self.round_number)
            else:
                if self.round_number == layer:
                    # Set a variable to block shuffling in duplicated round
                    self.session.vars['block_overwrite'] = True
                    # Shift questions between groups at each round
                    question_ids = self.subsession.set_next_questions(self.round_number)
                else:
                    # Shift questions between groups at each round
                    question_ids = self.subsession.set_next_questions(self.round_number)

                for p in self.subsession.get_players():
                    p.timestamp_begin = p.participant.vars['round_start_time'] = time.time()

            # Assign questions to layers based on shifted questions
            matrix = self.subsession.assign_layer_questions(matrix)


    # Set timeout to current value of session expiry
    def get_timeout_seconds(self):
        if 'expiry' in self.session.vars:
            return self.session.vars['expiry'] - time.time()
        else:
            # TODO: check that this should not be (self.round_number-1)?
            expiry = Constants.time_to_begin.timestamp() + self.round_number*Constants.time_to_answer_questions
            self.session.vars['expiry'] = expiry
            return expiry - time.time()

    # Time to display on custom wait page
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the time until the experiment begins
        time_left = self.get_timeout_seconds()

        # Set to zero if time is negative
        if str(time_left)[0] == "-": time_left = 0

        context.update({
            'time_left': round(time_left),
        })
        return context

    timeout_seconds = get_timeout_seconds

    timer_start = time.time()

class Question(Page):
    form_model = models.Player
    form_fields = ['food', 'drug','class_estimate', 'submitted_answer']

    # Only show for as many layers as we have active layers
    def is_displayed(self):
        if (self.round_number > 1) and (self.round_number <= self.session.vars['active_layers'] + 1):
            self.timestamp_begin = self.player.participant.vars['round_start_time'] = time.time()
        return (self.round_number > 1) and (self.round_number <= self.session.vars['active_layers'] + 1)

    def get_timeout_seconds(self):

        # Set timeout on pages to zero so that we can bypass extra questions
        if ('show_pages_after_results' in self.session.vars) and (self.session.vars['show_pages_after_results'] == False):
            self.session.vars['expiry'] = time.time()
            seconds = 0
        else:
            # Add question time allocation to current timeout
            expiry = Constants.time_to_begin.timestamp() + (self.round_number-1)*Constants.time_to_answer_questions
            self.session.vars['expiry'] = expiry
            seconds = expiry - time.time()
        return seconds


    def get_roles(self):
        u = self.group.get_role()
        prev = u.player.in_all_rounds()
        return prev

    def submitted_answer_choices(self):
       return ['negative','neutral','positive', 'timeout']

    def estimate_categorizer(self):
        if abs(self.player.class_estimate) < 34:
            self.player.submitted_answer = 'Neutral'
        elif self.player.class_estimate < 0:
            self.player.submitted_answer = 'Negative'
        else:
            self.player.submitted_answer = 'Positive'

        return self.player.submitted_answer

    def before_next_page(self):
        if self.timeout_happened:
            self.player.submitted_answer = 'timeout'
        else:
            self.estimate_categorizer()
        self.player.timestamp_answer = time.time()
        self.player.time_to_answer = time.time() - self.player.participant.vars['round_start_time']
        self.player.check_correct()


    def vars_for_template(self):

        # The experiment assignment for the individual
        experiment_id = self.player.group_id
        player_id = self.player.participant_id # Session id for player

        # Results from treatment layers
        if (self.round_number > 2) and (self.round_number <= self.session.vars['active_layers'] + 1):
            prev_layer = self.round_number - 1

            # Player stats from last layer
            prev_player_state = self.player.in_round(prev_layer)
            prev_player_action = {
                            'player_id': player_id,
                            'experiment_id': experiment_id,
                            'assignment': 't_e' + str(experiment_id) + '_l' + str(self.round_number - 1),
                            'network_layer': self.subsession.net_layer - 1,
                            'estimate': prev_player_state.class_estimate,
                            'class': prev_player_state.submitted_answer,
                            'question_id' : prev_player_state.question_id
            }

            # Collect all players from other groups
            not_self = self.player.get_others_in_subsession()
            grp = self.player.get_others_in_group()
            players = [x for x in not_self if x not in grp]

            # Get players in previous layer that answered current question_id
            prev_layer_action = []
            for p in players:
                prev_layer_state = p.in_round(prev_layer)

                # If player answered current question in previous round
                if int(prev_layer_state.question_id) == int(self.player.question_id):
                    prev_node_n = {
                                            'player_id' : prev_layer_state.participant_id,
                                            'estimate' : prev_layer_state.class_estimate,
                                            'class' : prev_layer_state.submitted_answer,
                                            'question_id' : prev_layer_state.question_id
                    }
                    prev_layer_action.extend([prev_node_n])

            invalid_estimates = ['timeout', '']
            n_mean = np.mean([i['estimate'] for i in prev_layer_action if i['class'] not in invalid_estimates and all([i['estimate'], i['class']]) is True])
            if not math.isnan(n_mean):
                n_mean = np.int(n_mean)
            else:
                n_mean = None

            try:
                agree = self.participant.vars['proceed_confirmation']
            except:
                agree = False
            self.participant.vars['agreed'] = agree

            v = {
                'player_prev': prev_player_action,
                'layer_prev': prev_layer_action,
                'layer_mean': n_mean,
                'agree_confirmation': agree,
            }

        # Results from control layers
        else:
            prev_player_action = {
                            'player_id': player_id,
                            'experiment_id': experiment_id,
                            'assignment': 'Control',
                            'network_layer': self.subsession.net_layer - 1,
                            'estimate': None,
                            'class': None,
                            'question_id' : None,
            }
            prev_layer_action = {
                                    'player_id' : 'Control',
                                    'estimate' : None,
                                    'class' : None,
                                    'question_id' : None,
            }

            try:
                agree = self.participant.vars['proceed_confirmation']
            except:
                agree = False
            self.participant.vars['agreed'] = agree

            v = {
                'player_prev': prev_player_action,
                'layer_prev': prev_layer_action,
                'layer_mean': 0.0,
                'agree_confirmation': agree,
            }

        return v

    timeout_seconds = get_timeout_seconds

class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True
    def get_timeout_seconds(self):
        return self.session.vars['expiry'] - time.time()

    def is_displayed(self):

        # Try to dynamically set last round using active layer
        if 'active_layers' in self.session.vars:
            display_round = self.session.vars['active_layers'] + 1
        else:
            display_round = Constants.num_rounds + 1

        # Show results on last round
        if self.round_number == display_round:

            # Get the maximum page index and round number from all participants
            if self.timeout_seconds() <= 0:
                self.session.vars['show_pages_after_results'] = False
                max_index, max_round_number = 0, 0

                # Set the index and page number for participants that are behind when the timer expires
                for p in self.subsession.get_players():
                    if p.participant._index_in_pages > max_index:
                        max_index = p.participant._index_in_pages #p.participant._max_page_index
                    if p.participant._round_number > max_round_number:
                        max_round_number = p.participant._round_number #p.participant._max_page_index

                # Players that are behind current max round and index
                for p in self.subsession.get_players():
                    if (p.participant._round_number != max_round_number) or (p.participant._index_in_pages != max_index):
                        p.participant._round_number = max_round_number
                        p.participant._index_in_pages = max_index

        return self.round_number == display_round

    timeout_seconds = get_timeout_seconds

class Results(Page):
    def is_displayed(self):
        if 'active_layers' in self.session.vars:
            return self.round_number == self.session.vars['active_layers'] + 1
        else:
            return self.round_number == Constants.num_rounds + 1

    def vars_for_template(self):

        # Try to dynamically set last round using active layer
        if 'active_layers' in self.session.vars:
            display_round = self.session.vars['active_layers'] + 1
        else:
            display_round = Constants.num_rounds + 1

        player_in_all_rounds = self.player.in_rounds(2,display_round)
        agree_round = self.player.in_rounds(1, 1)

        return {
            'agree_round': agree_round,
            'player_in_all_rounds': player_in_all_rounds,
            'questions_correct': sum([p.is_correct for p in player_in_all_rounds if p.is_correct is not None])
        }



page_sequence = [
    Introduction,
    StartShuffleWaitPage,
    WaitPage,
    Question,
    ResultsWaitPage,
    Results
]
