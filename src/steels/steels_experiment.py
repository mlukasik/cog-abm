"""
This module implements Steels exepriment.
"""
import logging
import random

import numpy as np

from cog_abm.core import Environment, Simulation
from cog_abm.core.interaction import Interaction
from cog_abm.core.environment import RandomStimuliChooser
from cog_abm.agent.sensor import SimpleSensor
from cog_abm.ML.core import Classifier
from cog_abm.extras.additional_tools import generate_simple_network
from cog_abm.extras.lexicon import Lexicon
from cog_abm.extras.tools import def_value

from steels import metrics
from metrics import DS_A

log = logging.getLogger('steels')


class ReactiveUnit(object):
    """ Reactive units are used in adaptive networks
    """

    def_sigma = 1.

    def __init__(self, central_value, sigma=None):
        self.central_value = central_value
        sigma = sigma or ReactiveUnit.def_sigma
        self.mdub_sqr_sig = np.longdouble(-0.5 / (sigma ** 2.))

    def value_for(self, x):
        """ Calculate reaction for given vector
        """
        a = self.central_value.distance(x) ** 2.
        w = np.exp(a * self.mdub_sqr_sig)
        return w

    def __eq__(self,  other):
        if isinstance(other,  ReactiveUnit):
            return other.central_value == self.central_value
        else:
            return False


class AdaptiveNetwork(object):
    """ Adaptive network is some kind of classifier
    """

    def_alpha = 0.1
    def_beta = 1.

    def __init__(self,  reactive_units=None, alpha=None, beta=None):
        """ Must be with weights !
        """
        self.units = reactive_units or []
        self.alpha = np.longdouble(alpha or AdaptiveNetwork.def_alpha)
        self.beta = np.longdouble(beta or AdaptiveNetwork.def_beta)

    def _index_of(self, unit):
        """ Finds index of given unit.
        Returns -1 if there is no such unit in this network
        """
        for i, (u, _) in enumerate(self.units):
            if u == unit:
                return i
        return -1

    def add_reactive_unit(self, unit, weight=1.):
        index = self._index_of(unit)
        weight = np.longdouble(weight)
        if index == -1:
            self.units.append((unit, weight))
        else:
            self.units[index] = (unit, weight)

    def reaction(self, data):
        return sum((w * u.value_for(data) for u, w in self.units))

    def _update_units(self, fun):
        tmp = [fun(u, w) for u, w in self.units]
        self.units = filter(lambda x: x is not None,  tmp)

    def remove_low_units(self, threshold=0.1 ** 30):
        self.units = [(u, w) for u, w in self.units if w >= threshold]

    def increase_sample(self, sample):
        self._update_units(lambda u, w:
            (u, min(np.longdouble(1.), w + self.beta * u.value_for(sample))))
                                # because we don't want to exceed 1

    #TODO: rewrite it to be in time O(1)
    def forgetting(self):
        self._update_units(lambda u, w: (u, self.alpha * w))
#               self.remove_low_units(0.1**50)
#               TODO: think about ^^^^^


class SteelsClassifier(Classifier):

    def __init__(self):
        self.categories = {}
        self.new_category_id = 0

    def add_category(self, sample=None, class_id=None):
        if class_id is None:
            class_id = self.new_category_id
            self.new_category_id += 1
            adaptive_network = AdaptiveNetwork()

        else:
            adaptive_network = self.categories[class_id]

        if sample is not None:
            adaptive_network.add_reactive_unit(
                ReactiveUnit(sample)
            )

        self.categories[class_id] = adaptive_network
        return class_id

    def del_category(self, category_id):
        del self.categories[category_id]

    def classify(self, sample):
        if len(self.categories) == 0:
            return None
        return max(self.categories.iteritems(),
            key=lambda kr: kr[1].reaction(sample))[0]

    def increase_samples_category(self, sample):
        category_id = self.classify(sample)
        self.categories[category_id].increase_sample(sample)

    def forgetting(self):
        for an in self.categories.itervalues():
            an.forgetting()

    def sample_strength(self, category_id, sample):
        return self.categories[category_id].reaction(sample)


class DiscriminationGame(Interaction):

    def_inc_category_treshold = 0.95

    def __init__(self, context_len=4, inc_category_treshold=None):
        self.context_len = context_len
        self.inc_category_treshold = def_value(inc_category_treshold,
            DiscriminationGame.def_inc_category_treshold)

    def num_agents(self):
        return 2

    def save_result(self, agent, result):
        agent.add_payoff("DG", int(result))

    def disc_game(self, agent, context, topic):
        ctopic = agent.sense_and_classify(topic)
        # no problem if ctopic is None => count>1 so it will add new category

        ccontext = [agent.sense_and_classify(c) for c in context]
        count = ccontext.count(ctopic)
        return (count == 1, ctopic)

    def learning_after(self, agent, topic, succ, ctopic=None):
        succ_rate = DS_A(agent)
        sensed_topic = agent.sense(topic)

        if succ:
            agent.state.classifier.increase_samples_category(sensed_topic)
        elif succ_rate >= self.inc_category_treshold:
            #agent.state.incrase_samples_category(topic)
            if ctopic is None:
                ctopic = agent.state.classifier.classify(sensed_topic)
            agent.state.classifier.add_category(sensed_topic, ctopic)

        else:
            agent.state.classifier.add_category(sensed_topic)

        # lower strength of memory
        agent.state.classifier.forgetting()

    def play_with_learning(self, agent, context, topic):
        succ, ctopic = self.disc_game(agent, context, topic)
        self.learning_after(agent, topic, succ, ctopic)
        return succ, ctopic, topic, context

    def play_save(self, agent, context, topic):
        succ, ctopic = self.disc_game(agent, context, topic)
        self.save_result(agent, succ)
        return succ, ctopic

    def play_learn_save(self, agent, context, topic):
        succ, ctopic, topic, context = \
                self.play_with_learning(agent, context, topic)

        #agent.add_inter_result(("DG", succ))
        self.save_result(agent, succ)
        return succ, ctopic, topic, context

    def get_setup(self, agent):
        env = agent.get_environment()
        context = env.get_stimuli(self.context_len)
        topic = context[0]
        # ^^^^ they are already shuffled - and needed when different classes
        return (context, topic)

    def interact_one_agent(self, agent, context=None, topic=None):
        if context is None or topic is None:
            context, topic = self.get_setup(agent)
        succ, _, _, _ = self.play_with_learning(agent, context, topic)
        self.save_result(agent, succ)
        return succ

    def interact(self, agent1, agent2):
        context, topic = self.get_setup(agent1)
        return (
            ("DG", self.interact_one_agent(agent1, context, topic)),
            ("DG", self.interact_one_agent(agent2, context, topic))
        )

    def __repr__(self):
        return "DiscriminationGame: context_len=%s;" \
            " inc_category_treshold=%s" % \
            (self.context_len, self.inc_category_treshold)


class GuessingGame(Interaction):
    # Based mostly on work "Colourful language and colour categories"
    # of Tony Belpaeme and Joris Bleys

    def __init__(self, disc_game=None, context_size=None):
        if disc_game is None:
            disc_game = DiscriminationGame()
            if context_size is not None:
                disc_game.context_len = context_size

        self.disc_game = disc_game

    def num_agents(self):
        return 2

    def save_result(self, agent, result):
        agent.add_payoff("GG", int(result))

    def learning_after_speaker_DG_fail(self, speaker, topic, ctopic):
        self.disc_game.learning_after(speaker, topic, False, ctopic)

    def learning_after_hearer_doesnt_know_word(self, topic, context, f,
            sp, hr, spctopic):
        #agent hr plays discrimination game on context and topic
        #The game returns: succ (boolean whether the game ended in success) 
        #and hectopic (the category to which topic belongs)
        succ, hectopic = self.disc_game.play_save(hr, context, topic)

        #if hr succesfuly played discrimination game:
        if succ:
            #add word f to category hectopic
            #=================================================================
            #MAYBE HERE IS A GOOD PLACE TO PUT ADDITIONAL CONDITION
            #=================================================================
            hr.state.lexicon.add_element(hectopic, f)
        #if hr does not discriminate the topic from context:
        else:
            #hr learns to discriminate:
            self.disc_game.learning_after(hr, topic, succ, hectopic)
            #get the category of hr to which topic belongs to after learning:
            class_id = hr.sense_and_classify(topic)
            #add word f to category hectopic in agent hr
            #=================================================================
            #MAYBE HERE IS A GOOD PLACE TO PUT ADDITIONAL CONDITION?
            #=================================================================
            hr.state.lexicon.add_element(class_id, f)

    def learning_after_game_succeeded(self, word, topic, context,
            sp, spc, hr, hrc):
        """
        sp - speaker
        spc - category of speaker for topic
        hr - hearer
        hrc - category of hearer for topic
        """
        sp.state.lexicon.inc_dec_categories(spc, word)
        # ^^ as in 4.2 1.(a)
        hr.state.lexicon.inc_dec_words(hrc, word)
        # ^^ as in 4.2 2.(a)

        for a in [sp, hr]:
            a.state.classifier.increase_samples_category(a.sense(topic))

    def learning_after_agents_mismatched_words(self, topic,
            sp, spw, spc,
            hr, hrw, hrc):
        sp.state.lexicon.decrease(spc, spw)
        # ^^ as in 4.2 1.(b)
        hr.state.lexicon.decrease(hrc, hrw)
        # ^^ as in 4.2 2.(b)

        # TODO: Not lexicon related:
        self.disc_game.learning_after(hr, topic, False)

    def guess_game(self, speaker, hearer):
        """
        The most important method: the guessing game logic.
        
        Each line explained by a comment.
        """

        #Get list of stimuli known by the speaker:
        env = speaker.get_environment()
        #Get a random list of stimuli from env of size self.disc_game.context_len:
        context = env.get_stimuli(self.disc_game.context_len)

        #The first element of this context is topic:
        topic = context[0]
        
        #The speaker plays the discrimination game on the selected context and topic. 
        #The game returns: succ (boolean whether the game ended in success) 
        #and spctopic (the speaker's category to which topic belongs)
        succ, spctopic = self.disc_game.play_save(speaker, context, topic)

        #If the speaker did not discriminate the topic from the rest of the context himself:
        if not succ:
            #learn by himself this discrimination:
            self.learning_after_speaker_DG_fail(speaker, topic, spctopic)
            #do not proceed further:
            return False
        
        #f = word that speaker uses to call the spctopic category
        f = speaker.state.word_for(spctopic)
        #if there is no word that speaker has for this category:
        if f is None:
            #a random word is chosen for this category and added:
            f = speaker.state.lexicon.add_element(spctopic)

        #hcategory = a category that hearer thinks of when using the word f:
        hcategory = hearer.state.category_for(f)
        #if there is no category for word f in hearer's memory:
        if hcategory is None:
            #the hearer learns a new word: 
            #if he discriminates topic from context, a new word is added
            #if he does not, he first learns to discriminate and only then learns a new word
            #=================================================================
            #MAYBE HERE IS A GOOD PLACE TO PUT THE CONDITION: INSIDE THE METHOD:
            #learning_after_hearer_doesnt_know_word
            #=================================================================
            self.learning_after_hearer_doesnt_know_word(topic,
                context, f, speaker, hearer, spctopic)
            return False

        #randomly shuffle the context: 
        random.shuffle(context)
        #Choose a stimulus from context, which is most characteristic to the hcategory 
        max_hr_sample = self.find_best_matching_sample_to_category(hearer,
            context, hcategory)

        # checking game result: is the strongest activated stimulus same as topic?
        succ = max_hr_sample == topic
        
        #if it is the same:
        if succ:
            #increase the confidence in word for topic in both speaker and hearer:
            #this is a symetric function from the perspective of speaker and hearer:
            self.learning_after_game_succeeded(f, topic, context,
                speaker, spctopic, hearer, hcategory)
            
        #if it is different:
        else:
            #decrease the confidence in word for topic in both speaker and hearer:
            #further, learning on hearer performed but without use of word f
            self.learning_after_agents_mismatched_words(topic,
                speaker, f, spctopic, hearer, f, hcategory)
        return succ

    def find_best_matching_sample_to_category(self, agent, samples, category):
        max_reaction, max_sample = float("-inf"), None
        for sample in samples:
            strength = agent.state.sample_strength(category,
                agent.sense(sample))
            if strength > max_reaction:
                max_reaction, max_sample = strength, sample
        return max_sample

    def interact(self, speaker, hearer):
        r = self.guess_game(speaker, hearer)
        self.save_result(speaker, r)
        self.save_result(hearer, r)
        return (("GG", r), ("GG", r))

    def __repr__(self):
        return "GuessingGame: %s" % self.disc_game


#class SteelsAgentState(AgentState):
class SteelsAgentState(object):

    def __init__(self, classifier):
        self.classifier = classifier

    def classify(self, sample):
        return self.classifier.classify(sample)

    def classify_pval(self, sample):
        return self.classifier.classify_pval(sample)

    def class_probabilities(self, sample):
        return self.classifier.class_probabilities(sample)

    def sample_strength(self, category, sample):
        return self.classifier.sample_strength(category, sample)


class SteelsAgentStateWithLexicon(SteelsAgentState):

    def __init__(self, classifier, initial_lexicon=None):
        super(SteelsAgentStateWithLexicon, self).__init__(classifier)
        self.lexicon = initial_lexicon or Lexicon()

    def category_for(self, word):
        return self.lexicon.category_for(word)

    def word_for(self, category):
        return self.lexicon.word_for(category)


#Steels experiment main part


def steels_uniwersal_basic_experiment(num_iter, agents,
        interaction, classifier=SteelsClassifier, topology=None,
        inc_category_treshold=None, dump_freq=50, stimuli=None, chooser=None,
        env=None):

    topology = topology or generate_simple_network(agents)

#       if stimuli == None:
#               stimuli = def_value(None, default_stimuli())

    if inc_category_treshold is not None:
        interaction.__class__.def_inc_category_treshold = inc_category_treshold

    #chooser = chooser or RandomStimuliChooser(use_distance=True, distance=distance)
    #env = environment#Environment(stimuli, chooser)
    for agent in agents:
        agent.env = env
    
    s = Simulation(topology, interaction, agents, colour_order=env.colour_order)
    res = s.run(num_iter, dump_freq)

#       import pprint
#       print pprint.pprint(error_counter)
    try:
#               s = sum(error_counter.values())
#               for k,v in error_counter.iteritems():
#                       print "%s: %s" % (k, float(v)/s)
        for a in agents:
            print "[%s]:%s" % (len(a.state.lexicon.known_words()),
                                                    a.state.lexicon.known_words())
        print "OK"
    except:
        pass

    return res


def steels_basic_experiment_DG(inc_category_treshold=0.95, classifier=None,
        interaction_type="DG", beta=1., context_size=4, stimuli=None,
        agents=None, dump_freq=50, alpha=0.1, sigma=1., num_iter=1000,
        topology=None, environment=None):

    classifier, classif_arg = SteelsClassifier, []

    # FIX THIS !!
    for agent in agents:
        agent.set_state(SteelsAgentState(classifier(*classif_arg)))
        agent.set_sensor(SimpleSensor())
        agent.set_fitness_measure("DG", metrics.get_DS_fitness())

    AdaptiveNetwork.def_alpha = float(alpha)
    AdaptiveNetwork.def_beta = float(beta)
    ReactiveUnit.def_sigma = float(sigma)
    DiscriminationGame.def_inc_category_treshold = float(inc_category_treshold)

    return steels_uniwersal_basic_experiment(num_iter, agents,
        DiscriminationGame(context_size), topology=topology,
            dump_freq=dump_freq, stimuli=stimuli, env=environment)


def steels_basic_experiment_GG(inc_category_treshold=0.95, classifier=None,
        interaction_type="GG", beta=1., context_size=4, stimuli=None,
        agents=None, dump_freq=50, alpha=0.1, sigma=1., num_iter=1000,
        topology=None, environment=None):

    classifier, classif_arg = SteelsClassifier, []
    #agents = [Agent(SteelsAgentStateWithLexicon(classifier()), SimpleSensor())\

    # FIX THIS !!
    classif_arg = def_value(classif_arg, [])
    for agent in agents:
        agent.set_state(SteelsAgentStateWithLexicon(classifier(*classif_arg)))
        agent.set_sensor(SimpleSensor())
        agent.set_fitness_measure("DG", metrics.get_DS_fitness())
        agent.set_fitness_measure("GG", metrics.get_CS_fitness())

    AdaptiveNetwork.def_alpha = float(alpha)
    AdaptiveNetwork.def_beta = float(beta)
    ReactiveUnit.def_sigma = float(sigma)
    DiscriminationGame.def_inc_category_treshold = float(inc_category_treshold)

    return steels_uniwersal_basic_experiment(num_iter, agents,
        GuessingGame(None, context_size), topology=topology,
            dump_freq=dump_freq, stimuli=stimuli, env = environment)
