Introduction
============

This software is intended to help in designing and running simulations involving agents and their cognitive capacities.

An agent-based model (ABM) (also sometimes related to the term multi-agent system or multi-agent simulation) is a class of computational models for simulating the actions and interactions of autonomous agents (both individual or collective entities such as organizations or groups) with a view to assessing their effects on the system as a whole. It combines elements of game theory, complex systems, emergence, computational sociology, multi-agent systems, and evolutionary programming. Monte Carlo Methods are used to introduce randomness [1]_.

The main aim of this project proposal is to describe how perceptually grounded categories can emerge among the members of a population to allow successful communication and improve the cognitive performance of both the group as a whole, and in parallel each individual member of the group. The language plays a crucial role in this process by naming games that pinpoint the constructed categories and allow for effective sharing of those categories within the community of interacting individuals. Therefore, it influences both the dynamics of categorization process, and the final selection of categories that are stable in time, and shared within all members of a population.

Humans are equipped in senses that are the physiological capacities within organisms that provide inputs for perception. The biological structure of senses, the way how they process incoming input from external world, the classification of available stimulus repertoires, categorization, overlapping of similar ones, and corrections of natural noise were studied by neurobiology, neuroscience, cognitive psychology, and human physiology. In last decades several mathematical models of human senses were proposed. Those models can be implemented as the software algorithms and allow for the construction of artificial agents that can be further used for modeling of the role of human perception system in categorization processes. In addition several works of Steels proved the possibility to couple those models of human perception with the dynamics of naming process, therefore simulating in silico how a perceptually grounded categorical repertoire can become sufficiently shared among the members of a population [2]_. The population of artificial agents was able to build color categories and share them so that one agent from the population can use the word to get another agent to pick out the proper object from a set of colored objects in a cognitive scene [3]_, [4]_.

In our research proposal we address two issues: the dynamics of categorization process (i.e. equilibration process, where the time dependent changes of categorical repertoire in a group are observed), and the role of naming (i.e. as the natural interaction substrate shared between individuals in a population). Each senses perception and categorization of the input sensory information will be investigated, comparison between artificial agents models and human populations will be performed. The several types of internal Agents architecture will be tested, including advanced learning algorithms, such as RC Reservoir Computing (ESN Echo State Networks, LSM Liquid State Machines [5]_). Moreover the set of interacting Agents itself will be modeled using our in-house modification of RC algorithm that builds the ensemble of interacting LSM. So-called Liquid State Society (LSS) framework is able to model more efficiently the category formation and exchange, naming process in social learning systems. This model will be later used in mixed human-agent populations for better understanding the coupling between the categorization and the naming processes simulated using the senses models. Such experimental setups allow for selecting, which factors are crucial for successful communication events, and proper calibration of the mathematical models of considered senses.


.. [1] see http://en.wikipedia.org/wiki/Agent-based_model
.. [2] Steels, L. and Belpaeme, T. (2005) Coordinating Perceptually Grounded Categories through Language: A Case Study for Colour. Behavioral and Brain Sciences, 28(4):469—89;
.. [3] Steels, L. and Baillie, J-C. (2003) Shared Grounding of Event Descriptions by Autonomous Robots. Robotics and Autonomous Systems, 43(2-3):163-173.
.. [4] Steels, L. (2003) Evolving grounded communication for robots. Trends in Cognitive Science, 7(7):308-312 July 2003.
.. [5] Maass W., Natschlaeger T., Markram H. (2002) Real-time computing without stable states: A new framework for neural computation based on perturbations. Neural Computation, 14(11):2531-2560.


Documentation
=============

Can be found on ReadTheDocs_.

.. _ReadTheDocs: http://cog-abm.readthedocs.org


Usage
=====

To run this software you need Python in version 2.x (3.x is not supported).

There are mostly libraries which helps you develop your own simulations. Sample simulation you might find in src/steels/ folder. As of version 0.3 all parameters and configuration of simulations is stored in XML files.


Steels experiment
-----------------
An example experiment. It was described in work of Steels, L. and Belpaeme, T. (2005).
Sample configuration is in files src/simulation.xml  and in src/simulation2.xml
To run one go to src folder and run:
python steels/steels_main.py -p "simulation.xml"
this should generate some files – some of them are used by presenter which visualizes result by showing agents categorization at given points, and one is used by analyzer

Usage: python steels_main.py [options]

Options:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity (specify multiple times for more)
  -f FILE, --file=FILE  output file with results
  -p PARAM_FILE, --params_file=PARAM_FILE
                        file with parameters


Analyzer
--------
Helps you analyze data generated during simulation. Normally it outputs data as table separated with tabulation, but with option -c you can change output to chart. Important thing: if you would like to see number of iteration when given statistic where taken you should specify to use statistic “it” (see examples)

Usage: python analyzer.py [-c] [-v] -f FILE statistic1 statistic2 ...
where statistic in {cc;CSA;it;cv;CS;DS;DSA}

Options:
  -h, --help            show this help message and exit
  -v, --verbose         increase verbosity (specify multiple times for more)
  -c, --chart           specifies output to be a chart
  -f FILE, --file=FILE  input file with results. THIS OPTION IS NECESSARY!
  --xlabel=XLABEL       Label of x-axis
  --ylabel=YLABEL       Label of y-axis


Presenter
---------
This program uses files with extension .pout . It presents agents categorization at given iteration.
To run it go to src/presenter
Usage: munsell_palette.py [options]

Options:
  -h, --help            show this help message and exit
  -a AGENTS, --agents=AGENTS
                        Number of agents viewed
  -d DIRECTORY, --directory=DIRECTORY
                        Directory with input data
  -f FIND_FOCAL, --findfocal=FIND_FOCAL
                        Determines which 'find_focal' algorithm will
                        be used ('normal' as default or 'strength_based')
  -l LEGEND, --legend=LEGEND
                        Type true to show language sharing


Example of full “usage path”
----------------------------

Run simulation. From /src/steels run:
python steels_main.py -p "simulation.xml"

now see result in chart:
python analyzer.py -f \*.result -c it DS CS --xlabel="iteration" --ylabel "discriminative success & communicative success"

to see categorization:
from /src/presenter run:
python munsell_palette.py -d ../ -a 10 --findfocal strength_based -l t


Required librares (easy to install with pip)
============================================

- numpy
- scipy
- progressbar
- matplotlib (for charts)
- grapefruit (built in?)
- pygraph (named python-graph-core)


Unofficial tutorial
===================

Can be found here_.

.. _here: https://github.com/kkonrad/cog-abm-tutorial



Authors
=======

:Authors:
    *Programming:* Konrad Kurdej, Michał Łukasik, Marek Maj

    *Mentoring:* Dariusz Plewczyński, Franciszek Rakowski


Origins
=======

This software is fork of **COG-ABM** from account **cogcomp**.


License
=======

This software is dual-licensed.

By commercial usage we mean:

- selling software that uses any part of this software
- providing service that uses any part of this software

With the restriction of non-commercial usage you can use this software with application of AGPL-3.0 license. See **NC_LICENSE.rst** for more information.


License for commercial usage is under development.
