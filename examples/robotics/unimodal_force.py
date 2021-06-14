import sys
import os
sys.path.insert(0, os.getcwd())

import time

import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import yaml
import os
from tqdm import tqdm

from fusions.robotics.sensor_fusion import SensorFusionSelfSupervised,roboticsConcat
from unimodals.robotics.encoders import (
    ProprioEncoder, ForceEncoder, ImageEncoder, DepthEncoder, ActionEncoder,
)
from unimodals.common_models import MLP
from unimodals.robotics.decoders import ContactDecoder
from training_structures.Supervised_Learning import train, test
from robotics_utils import set_seeds

from datasets.robotics.data_loader import get_data
from torch.utils.data import DataLoader
from torch.utils.data.sampler import SubsetRandomSampler
from torchvision import transforms


class selfsupervised:
    def __init__(self, configs):

        # ------------------------
        # Sets seed and cuda
        # ------------------------
        use_cuda = True

        self.configs = configs
        self.device = torch.device("cuda" if use_cuda else "cpu")

        set_seeds(configs["seed"], use_cuda)

        self.encoders = [
            ForceEncoder(configs['zdim'], alpha=configs['force']),
            ActionEncoder(configs['action_dim']),
        ]
        """
        self.fusion = SensorFusionSelfSupervised(
            device=self.device,
            encoder=configs["encoder"],
            deterministic=configs["deterministic"],
            z_dim=configs["zdim"],
        ).to(self.device)
        """
        self.fusion = roboticsConcat("simple")
        #self.head = ContactDecoder(z_dim=configs["zdim"], deterministic=configs["deterministic"])
        self.head=MLP(288,128,2)
        self.optimtype = optim.Adam

        # losses
        self.loss_contact_next = nn.BCEWithLogitsLoss()

        self.train_loader, self.val_loader = get_data(self.device, self.configs,"/home/pliang/multibench/MultiBench-robotics/",unimodal='force')

    def train(self):
        print(len(self.train_loader.dataset), len(self.val_loader.dataset))
        with open('train_dataset.txt', 'w') as f:
            for x in self.train_loader.dataset.dataset_path:
                f.write(f'{x}\n')
        with open('val_dataset.txt', 'w') as f:
            for x in self.val_loader.dataset.dataset_path:
                f.write(f'{x}\n')
        train(self.encoders, self.fusion, self.head,
              self.train_loader, self.val_loader,
              15,
              optimtype=self.optimtype,
              lr=self.configs['lr'])

with open('examples/robotics/training_default.yaml') as f:
    configs = yaml.load(f)

selfsupervised(configs).train() 
