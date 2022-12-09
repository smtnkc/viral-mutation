# Learning the language of viral evolution and escape

This repository contains the analysis code, links to the data, and pretrained models for the paper ["Learning the language of viral evolution and escape"](https://science.sciencemag.org/content/371/6526/284) by Brian Hie, Ellen Zhong, Bonnie Berger, and Bryan Bryson (2021).

### Data

You can download the [relevant datasets](http://cb.csail.mit.edu/cb/viral-mutation/data.tar.gz) (including training and validation data) using the commands
```bash
wget http://cb.csail.mit.edu/cb/viral-mutation/data.tar.gz
tar xvf data.tar.gz
```
within the same directory as this repository.

### Dependencies

The major Python package requirements and their tested versions are in [requirements.txt](requirements.txt).

Our experiments were run with Python version 3.7 on Ubuntu 18.04.

## SARS-CoV-2 Spike Experiments

Key results from experiments can be found in the [`results/`](results) directory and can be reproduced with the commands below. The [`models/`](models) directory contains pretrained models used in the analyses. To run the experiments below, download the data (instructions above). For SARS-CoV-2 Spike, _in silico_ fitness and escape model inference (``--test``) takes around **~10 hours** on a system with 400 GB of CPU RAM and 32 GB of GPU RAM.

#### Semantic embedding UMAPs and log files with statistics can be generated with the command
```bash
python bin/cov.py bilstm --checkpoint models/cov.hdf5 --embed
```

#### Single-residue escape prediction using validation data from [Baum et al. (2020)](https://science.sciencemag.org/content/early/2020/06/15/science.abd0831) and DMS data from [Greaney et al. (2020)](https://www.biorxiv.org/content/10.1101/2020.09.10.292078v1.full.pdf) can be done with the command
```bash
python bin/cov.py bilstm --checkpoint models/cov.hdf5 --semantics
```

:warning: Semantic analyses take **< 80 hours** (Baum=65h and Greaney=11h) on an [barbun-cuda](https://docs.truba.gov.tr/TRUBA/kullanici-el-kitabi/hesaplamakumeleri.html#barbun-cuda) node (2 x 16Gb GPU).

#### Combinatorial fitness experiments measuring correlation with grammaticality and semantic change using data from [Starr et al. (2020)](https://jbloomlab.github.io/SARS-CoV-2-RBD_DMS) can be done with the command
```bash
python bin/cov.py bilstm --checkpoint models/cov.hdf5 --combfit
```

:warning: Combfit analyses take **< 180 hours** on an [akya-cuda](https://docs.truba.gov.tr/TRUBA/kullanici-el-kitabi/hesaplamakumeleri.html#akya-cuda) node (4 x 16Gb GPU).

#### Experiments measuring grammaticality and semantic change of a SARS-CoV-2 reinfection event documented by [To et al. (2020)](https://academic.oup.com/cid/advance-article/doi/10.1093/cid/ciaa1275/5897019) can be done with the command
```bash
python bin/cov.py bilstm --checkpoint models/cov.hdf5 --reinfection
```

#### Training a new model on coronavirus spike sequences can be done with the command
```bash
python bin/cov.py bilstm --train
```

:warning: Training takes **< 15 hours per epoch** on an [akya-cuda](https://docs.truba.gov.tr/TRUBA/kullanici-el-kitabi/hesaplamakumeleri.html#akya-cuda) node (4 x 16Gb GPU).

#### Testing a new model on coronavirus spike sequences can be done with the command
```bash
python bin/cov.py bilstm --checkpoint models/cov.hdf5 --test
```

:warning: Testing takes **< 6 hours** on an [akya-cuda](https://docs.truba.gov.tr/TRUBA/kullanici-el-kitabi/hesaplamakumeleri.html#akya-cuda) node (4 x 16Gb GPU).

## Omicron Spike experiments

Evaluating the Coronaviridae language model on major SARS-CoV-2 Spike variants, including Omicron, as well as on SARS-CoV-1 Spike, can be done with the commands
```bash
python bin/cov_fasta.py \
    examples/example_wt.fa \
    examples/example_target.fa \
    --checkpoint models/cov.hdf5 | tail -n+31 \
    > cov_fasta.log
python bin/plot_variants.py cov_fasta.log
```

## Benchmarking experiments

Performing a sweep of escape cutoffs to compare the AUC of CSCS to that of baseline methods can be done with the command
```bash
bash bin/benchmark_escape.sh
```

### Questions

For questions, please use the [GitHub Discussions](https://github.com/brianhie/viral-mutation/discussions) forum. For bugs or other problems, please file an [issue](https://github.com/brianhie/viral-mutation/issues).

