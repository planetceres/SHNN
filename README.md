## Supervised Human Neural Network (SHNN)

This repository holds the source code for a research experiment conducted in 2017 called the Supervised Human Neural Network (SHNN).

The paper can be downloaded in pdf format here:
[Supervised_Human_Neural_Network.pdf](./Supervised_Human_Neural_Network.pdf)

### Summary

In order to explore how information moves through human networks we use a
structured network design from artificial neural networks to impose
a deliberate structure on human networks. This acts to quantify how strategic arrangement
might affect information transmission between units in a coordinated task. We hypothesize
that human networks might perform more accurate classifications simply as a result of how
units acting as nodes are structurally configured.


![Network Design](./img/network_design_a.png)


### Code

The experiment was conducted on Amazon's Mechanical Turk platform using a modified
version of [Otree](https://github.com/oTree-org/oTree), a platform for social science
experiments.

You can run the experiment for yourself using the following commands:

```
cd src
pip3 install -U otree-core
otree resetdb
otree runserver
```

See the [Otree](https://github.com/oTree-org/oTree) documentation for more details.
