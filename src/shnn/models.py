from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from django import forms
from collections import defaultdict, OrderedDict
import random
from datetime import datetime

author = 'Matt Shaffer and Adam Lenart'

doc = """
A classification task that reads its questions from a spreadsheet
(see *.csv in this directory) and constructs a human neural network to pass
information between layers.
There is 1 question per page; the number of pages in the game
is determined by the number of layers in the network.
See the comments below about how to randomize the order of pages.
"""

class Constants(BaseConstants):
    welcome_template = 'shnn/Welcome.html'
    name_in_url = 'shnn'

    # Time to begin experiment (UTC time is 8 ahead of PST)
    time_to_begin = datetime.strptime('2017-12-22 03:50:00', '%Y-%m-%d %H:%M:%S')
    time_of_experiment = time_to_begin.timestamp()
    time_to_answer_questions = max_time_for_waitpages = 500

    # EXP: Change before experiment to appropriate group size
    players_per_group = 8
    n_layers = 5
    baseline_layers = 1 # no treatment for all rounds in baseline_layers

    # N Treatment layers + 1 control
    num_rounds = n_layers + 1
    randomization_round = 1

    questions = []
    with open('shnn/labeled_data_selected.tsv') as f:
        for i, row in enumerate(f):
            # skip header line
            if i == 0:
                continue
            id, label, _, drug, food, question = row.strip().split('\t')
            questions.append(OrderedDict({
                                        'id':id,
                                        'label': label,
                                        'drug': drug,
                                        'food': food,
                                        'text': question
                                        }.items()))

    random.shuffle(questions)

    class_scale_max = c(100)
    class_scale_min = c(-100)

    # Break questions into (n_layers + 1) ~ [n_layers + control] subgroups
    def question_subgrouping(questions, n_layers):

        total_layers = n_layers + 1
        total_layers = total_layers*2 # (this is to make enough layers for mturk)
        question_group = []

        for l in range(0, total_layers):

            # number of questions in layer
            sample_len = int(len(questions)/(total_layers - l))

            # randomly sample and assign questions to layer l
            idx = random.sample(questions, sample_len)
            for x in idx: x.update({'layer': l})
            question_group = question_group + idx

            # remove questions that already belong to a group from questions set
            questions = [x for x in questions if x not in idx]
        return question_group

    # grouped questions
    question_ids = []
    questions = question_subgrouping(questions, n_layers)


class Subsession(BaseSubsession):

    net_layer = models.PositiveIntegerField(
        doc="Layer in Network"
    )

    def creating_session(self):
        self.net_layer = self.round_number
        self.session.vars['question_ids_active'] = []
        self.session.vars['question_ids_inactive'] = []
        self.session.vars['active_layers'] = Constants.num_rounds

        # First round is the control layer
        if self.round_number == 2:

            # Get randomized group assignments matrix
            for m in self.get_group_matrix(): print(m)

            # Set the questions for the session as the questions
            self.session.vars['questions'] = Constants.questions

            for p in self.get_players():
                question_data = random.sample(self.session.vars['questions'], 1)
                question_data = question_data[0]
                p.question_id = question_data['id']
                p.food = question_data['food']
                p.drug = question_data['drug']
                p.question = question_data['text']
                p.solution = question_data['label']


    # Get questions for each group in control layer
    def first_question(self, round_number, group_idx):
        quest = self.session.vars['questions']

        try:
            q = next(x for x in quest if x['layer'] == group_idx)
        except Exception as e:
            print("Questions by layer failed, selecting by global method: ", e)
            q = next(x for x in quest)
        return q

    # Set the questions for next layer in active network
    def set_next_questions(self, round_number):
        shift_n = round_number - 3

        # get previous round
        prev_round = self.in_previous_rounds()[shift_n]
        # get question ids from previous round
        idx_active = prev_round.session.vars['question_ids_active']

        # shift all questions to the left by index of 1
        idx_active.append(idx_active.pop(0))

        return idx_active

    # Set the questions from the last layer in active network
    def set_prev_questions(self, round_number):
        return self.session.vars['question_ids_active']

    # Retrieve next question by matching question id and returning first match
    def get_next_question(self, qid):
        quest = self.session.vars['questions']
        for x in quest:
            if x['id'] == qid:
                q = x
        return q

    # Retrieve next question by matching question id and returning first match
    def get_next_random_question(self, qid):
        quest = self.session.vars['questions']

        # Remove used questions from possible pool of questions
        q_set = [x for x in quest if x not in qid]

        # Sample one question
        q = random.sample(q_set, 1)
        return q[0]

    # shuffle players and return the group matrix
    def shuffle_players(self):
        self.group_randomly()
        matrix = self.get_group_matrix()
        return matrix

    # Randomize and assign questions to groups in pre-treatment layer
    def assign_control_questions(self, matrix):

        # Number of active layers that we set in ShuffleWaitPage
        active = self.session.vars['active_layers']

        # Assign each experiment group a control question
        for idx, group in enumerate(matrix):

            # Get random question for group with id=idx
            question_data = self.first_question(self.round_number, idx)

            # Save the questions we are using so that we can retrieve them for following rounds
            if idx in range(active):
                self.session.vars['question_ids_active'].append(question_data['id'])
            else:
                self.session.vars['question_ids_inactive'].append(question_data['id'])

            # Assign the question to all participants in the group
            for p in group:
                p.question_id = question_data['id']
                p.food = question_data['food']
                p.drug = question_data['drug']
                p.question = question_data['text']
                p.solution = question_data['label']

                # Label each participant as being in the active group or inactive group
                if idx in range(active):
                    p.participant.vars['active_group'] = True
                else:
                    p.participant.vars['active_group'] = False

        return self.get_group_matrix()

    def assign_layer_questions(self, matrix):

        # Get the questions that have been randomly chosen for the experiment
        self.question_ids_active = self.session.vars['question_ids_active']
        self.question_ids_inactive = self.session.vars['question_ids_inactive']

        # Get number or active layers
        active = self.session.vars['active_layers']

        # Assign each experiment group the treament question that matches shifted question_ids
        for idx, group in enumerate(matrix):
            # Shift the questions by one group index
            if idx in range(active):
                question_data = self.get_next_question(self.question_ids_active[idx])
            else:
                # Randomize questions for 'inactive' groups
                inactive_ids = self.session.vars['question_ids_inactive']
                question_data = self.get_next_random_question(inactive_ids)
                # append id of chosen question to ids so we can take the questions out of circulation
                inactive_ids.append(question_data)

            for p in group:
                p.question_id = question_data['id']
                p.food = question_data['food']
                p.drug = question_data['drug']
                p.question = question_data['text']
                p.solution = question_data['label']

        return self.get_group_matrix()


class Group(BaseGroup):
    def get_role_in_group(self, id_in_group):
        r = 'id_in_group_' + str(id_in_group)
        return self.get_player_by_role(r)

    def get_group_id(self, group_id):
        r = 'experiment_' + str(group_id)
        return self.get_player_by_role(r)

    def player_by_id(self, n):
        return self.get_player_by_id(n)

class Player(BasePlayer):

    time_of_experiment = Constants.time_to_begin

    def get_group_id(self):
        return 'experiment_' + str(self.group_id)

    def role_id_in_group(self):
        return 'id_in_group_' + str(self.id_in_group)

    def other_player(self):
        return self.get_others_in_group()[0]

    # This is from quiz template, and needs to be modified for shnn
    def current_question(self):
        return self.session.vars['questions'][self.round_number - 1]

    def check_correct(self):
        # If participant exceeds time limit to make a selection, they get no credit
        self.is_correct = self.submitted_answer.lower() == self.solution.lower()
        self.payoff += self.is_correct
        return self.is_correct

    group_id_for_round = get_group_id
    role_id = role_id_in_group
    partners = other_player


    # Field for agreeing to complete the experiment after all participants have arrived
    # used for sorting active vs inactive players
    proceed_confirmation = models.BooleanField()


    question_id = models.PositiveIntegerField()
    question = models.CharField()
    solution = models.CharField()
    submitted_answer = models.CharField(widget=widgets.RadioSelect, initial = 'timeout')
    food = models.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    drug = models.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    is_correct = models.BooleanField()
    class_estimate = models.IntegerField(
        min=Constants.class_scale_min, max=Constants.class_scale_max,
        doc="Classification estimation by the player")
    time_to_answer = models.FloatField()
    timestamp_answer = models.FloatField()
    timestamp_begin = models.FloatField()
