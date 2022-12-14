# AC-CAR

Requirements: PyTorch 1.7.0, Python 3.6

This document summarizes the installation instructions and steps for developing defense against adversarial malware variants via sequential decision making named AC-CAR in PyTorch. The code extends three open-source repositories: (1) A modified version of Transformers library (https://huggingface.co/docs/transformers/installation), whcih includes GPT lanugage model and corresponding operations, (2) the OpenAI Gym (https://github.com/openai/gym) as the reinforcement learning infrastructure, and (3) an extended version of malware_env (https://github.com/endgameinc/gym-malware), which is based on OpenAI's Gym RL environment. For binary executable manipulations the code leverages lief libraray (https://github.com/lief-project/LIEF).

## Acknowledgement
We are grateful to Yash Chandak from the University of Massachusetts for the helpful discussion and sharing the implementation of [their work](https://proceedings.mlr.press/v97/chandak19a.html) with us.

## Installation Guide

Here are the recommended steps to create a virtual environment and install the requirements.

**virtual environment**

        conda create -n ACCAR python=3.6

**OPenAI Gym**

        pip3 install gym==0.9.2

**PyTorch (Having a GPU is Not necessary - the code can work on both CPU and GPU)**

        conda install pytorch==1.7.0 cpuonly -c pytorch

**scikit-learn**

        pip3 install scikit-learn==0.18.2

**LIEF**

        pip3 install https://github.com/lief-project/LIEF/releases/download/0.7.0/linux_lief-0.7.0_py3.6.tar.gz

**UPX for file compression**

        chmod +wrx /accar/torch/gym_malware/envs/controls/UPX/upx

Note: Some absolute paths of files may need to be changed to your local file system.

## Modified Transformers and GPT
We modified the [Transformers](https://huggingface.co/docs/transformers/installation) code to incorporate the RL-Augmented Top-k Sampling. To install the modified version, please download and navigate to our transformers folder and install it as follows:

        cd transformers

        pip install -e .

A pre-trained GPT on benign executables resides under "/model_hex."


## Data

The data was obtained from VirusTotal and cannot be shared in a public repository. However, AC-CAR operates on any Windows malware files. To give your malware data as seeds to generate adversarial variants and enhance defense, simply copy your malware files into the below location:

"/gym-malware/gym_malware/envs/utils/samples".

The generated adversarial samples will be stored in "/gym-malware/evaded/blackbox."

## Malware Detector Models

Pretrained MalConv, NoNeg and Ember LightGBM malware detector models are included in the code at /gym-malware/gym_malware/envs/utils under malconv.checkpoint, nonneg.checkpoint, and gradient_boosting.pkl.

## Execution

Run "/accar/Src/run.py."


