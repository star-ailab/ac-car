import numpy as np
import torch
from torch import float32
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
from Src.Utils.utils import NeuralNet, pairwise_distances, pairwise_hyp_distances, squash, atanh
from Src.Utils import Basis

class Action_representation(NeuralNet):
    def __init__(self,
                 state_dim,
                 action_dim,
                 config):
        super(Action_representation, self).__init__()

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config
        self.norm_const = np.log(self.action_dim)

        # Action embeddings to project the predicted action into original dimensions
        if config.true_embeddings:
            embeddings = config.env.get_embeddings() #motions.copy()
            self.reduced_action_dim = np.shape(embeddings)[1]
            maxi, mini = np.max(embeddings), np.min(embeddings)
            embeddings = ((embeddings - mini)/(maxi-mini))*2 - 1  # Normalize to (-1, 1)

            self.embeddings = Variable(torch.from_numpy(embeddings).type(float32), requires_grad=False)
        else:
            self.reduced_action_dim = config.reduced_action_dim
            if self.config.load_embed:
                try:
                    init_tensor = torch.load(self.config.paths['embedding'])['embeddings']
                except KeyError:
                    init_tensor = torch.load(self.config.paths['embedding'])['embeddings.weight']
                assert init_tensor.shape == (self.action_dim, self.reduced_action_dim)
                print("embeddings successfully loaded from: ", self.config.paths['embedding'])
            else:
                init_tensor = torch.rand(self.action_dim, self.reduced_action_dim)*2 - 1   # Don't initialize near the extremes.
            
            ## Read the embeddings
            self.embeddings = torch.load("../model_hex/wte.pt")

            ##self.embeddings = torch.nn.Parameter(init_tensor.type(float32), requires_grad=True)

        # One layer neural net to get action representation
        self.fc1 = nn.Linear(self.state_dim*2, self.reduced_action_dim)

        print("Action representation: ", [(name, param.shape) for name, param in self.named_parameters()])
        self.optim = config.optim(self.parameters(), lr=self.config.embed_lr)
    
    def get_match_scores(self, action):
        # compute similarity probability based on L2 norm
        embeddings = self.embeddings
        if not self.config.true_embeddings:
            embeddings = torch.tanh(embeddings)

        # compute similarity probability based on L2 norm
        similarity = - pairwise_distances(action, embeddings)  # Negate euclidean to convert diff into similarity score

        # compute similarity probability based on dot product
        # similarity = torch.mm(action, torch.transpose(embeddings, 0, 1))  # Dot product

        return similarity

    def get_best_match(self, action):
        similarity = self.get_match_scores(action)
        val, pos = torch.max(similarity, dim=1)
        return pos.cpu().item() #data.numpy()[0]

    def get_embedding(self, action):
        # Get the corresponding target embedding
        action_emb = self.embeddings[action]
        if not self.config.true_embeddings:
            action_emb = torch.tanh(action_emb)
        return action_emb

    ## g: Should be g
    def forward(self, state1, state2):
        # concatenate the state features and predict the action required to go from state1 to state2
        state_cat = torch.cat([state1, state2], dim=1)
        x = torch.tanh(self.fc1(state_cat))
        # x = self.fc1(state_cat)
        # x = F.tanh(self.fc2(x))
        return x

    def unsupervised_loss(self, s1, a, s2, normalized=True):
        x = self.forward(s1, s2)
        similarity = self.get_match_scores(x)  # Negative euclidean
        if normalized:
            loss = F.cross_entropy(similarity, a, reduction='elementwise_mean')/self.norm_const \
                   + self.config.emb_reg * torch.pow(self.embeddings, 2).mean()/self.reduced_action_dim
        else:
            loss = F.cross_entropy(similarity, a, reduction='elementwise_mean') \
                   + self.config.emb_reg * torch.pow(self.embeddings, 2).mean()
        return loss



class Action_representation_deep(Basis.NN_Basis):
    def __init__(self, action_dim, config):
        super(Action_representation_deep, self).__init__(config=config)

        self.state_dim = self.feature_dim
        self.action_dim = action_dim
        self.config = config
        self.norm_const = np.log(self.action_dim)

        # Action embeddings to project the predicted action into original dimensions
        if config.true_embeddings:
            embeddings = config.env.get_embeddings()
            self.reduced_action_dim = np.shape(embeddings)[1]
            maxi, mini = np.max(embeddings), np.min(embeddings)
            embeddings = ((embeddings - mini)/(maxi-mini))*2 - 1  # Normalize to (-1, 1)

            self.embeddings = Variable(torch.from_numpy(embeddings).type(float32), requires_grad=False)
        else:
            self.reduced_action_dim = config.reduced_action_dim
            if self.config.load_embed:
                try:
                    init_tensor = torch.load(self.config.paths['embedding'])['embeddings']
                except KeyError:
                    init_tensor = torch.load(self.config.paths['embedding'])['embeddings.weight']
                assert init_tensor.shape == (self.action_dim, self.reduced_action_dim)
                print("embeddings successfully loaded from: ", self.config.paths['embedding'])
            else:
                init_tensor = torch.rand(self.action_dim, self.reduced_action_dim)*2 - 1   # Don't initialize near the extremes.

            self.embeddings = torch.nn.Parameter(init_tensor.type(float32), requires_grad=True)

        # One layer neural net to get action representation
        self.fc1 = nn.Linear(self.state_dim*2, self.reduced_action_dim)
        # self.fc2 = nn.Linear(128, self.reduced_action_dim)

        print("Action representation: ", [(name, param.shape) for name, param in self.named_parameters()])
        self.optim = config.optim(self.parameters(), lr=self.config.embed_lr)

    def get_match_scores(self, action):
        # compute similarity probability based on L2 norm
        embeddings = self.embeddings
        if not self.config.true_embeddings: #TODO
            embeddings = F.tanh(embeddings)

        # compute similarity probability based on L2 norm
        similarity = - pairwise_distances(action, embeddings)  # Negate euclidean to convert diff into similarity score

        # compute similarity probability based on dot product
        # similarity = torch.mm(action, torch.transpose(embeddings, 0, 1))  # Dot product

        return similarity

    def get_best_match(self, action):
        similarity = self.get_match_scores(action)
        val, pos = torch.max(similarity, dim=1)
        return pos.cpu().item() #data.numpy()[0]

    def get_embedding(self, action):
        # Get the corresponding target embedding
        action_emb = self.embeddings[action]
        if not self.config.true_embeddings:
            action_emb = F.tanh(action_emb)
        return action_emb

    def forward(self, state1, state2):
        # concatenate the state features and predict the action required to go from state1 to state2
        state1 = super(Action_representation_deep, self).forward(state1)
        state2 = super(Action_representation_deep, self).forward(state2)

        state_cat = torch.cat([state1, state2], dim=1)
        x = F.tanh(self.fc1(state_cat))
        # x = self.fc1(state_cat)
        # x = F.tanh(self.fc2(x))
        return x

    def unsupervised_loss(self, s1, a, s2):
        x = self.forward(s1, s2)
        similarity = self.get_match_scores(x)  # Negative euclidean
        loss = F.cross_entropy(similarity, a, size_average=True)/self.norm_const \
               + self.config.emb_reg * torch.pow(self.embeddings, 2).mean()/self.reduced_action_dim
        return loss



class Action_representation_sparse(NeuralNet):
    # TODO: update code to support sparse. Keep the embeddings dense during phase1 training, switch to sparse version for online.
    # TODO: Instead of indexing, directly use embeddings.weight when emb_fraction is almost 1.0

    def __init__(self,
                 state_dim,
                 action_dim,
                 config):
        super(Action_representation_sparse, self).__init__()

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config
        self.fraction = self.config.emb_fraction
        self.pos_zero = torch.tensor([0], dtype=torch.long)
        self.norm_const = np.log(self.action_dim)

        # Action embeddings to project the predicted action into original dimensions
        if config.true_embeddings:
            embeddings = config.env.motions.copy()
            self.reduced_action_dim = np.shape(embeddings)[1]
            maxi, mini = np.max(embeddings), np.min(embeddings)
            embeddings = ((embeddings - mini)/(maxi-mini))*2 - 1  # Normalize to (-1, 1)

            self.embeddings = nn.Embedding(self.action_dim, self.reduced_action_dim, sparse=False)
            self.embeddings.weight = torch.nn.Parameter(torch.from_numpy(embeddings).type(config.dtype))
            self.embeddings.weight.requires_grad = False
        else:
            self.reduced_action_dim = config.reduced_action_dim
            if self.config.load_embed:
                init_tensor = torch.load(self.config.paths['embedding'])['embeddings.weight']
                assert init_tensor.shape == (self.action_dim, self.reduced_action_dim)
                print("embeddings successfully loaded")
            else:
                # init_tensor = torch.rand(self.action_dim, self.reduced_action_dim)*4 - 2  # Tanh of this range will be mostly around (-1, 1)
                init_tensor = torch.rand(self.action_dim, self.reduced_action_dim)*2 - 1  # Don't initialize near the extremes.

            self.embeddings = nn.Embedding(self.action_dim, self.reduced_action_dim, sparse=False) #
            self.embeddings.weight = torch.nn.Parameter(init_tensor.type(float32).to(self.config.device), requires_grad=True)

        # One layer neural net to get action representation
        self.fc1 = nn.Linear(self.state_dim*2, self.reduced_action_dim)
        # self.fc2 = nn.Linear(128, self.reduced_action_dim)

        print("Action representation: ", [m for m, _ in self.named_parameters()])
        parameters = filter(lambda p: p.requires_grad, self.parameters())
        self.optim = config.optim(parameters, lr=self.config.actor_lr)

    def set_embedding(self, embedding):
        self.embeddings = embedding

    def get_embed_param(self):
        return self.embeddings

    def get_match_scores(self, action, random_set):
        embeddings = self.embeddings(random_set)
        if not self.config.true_embeddings:
            embeddings = F.tanh(embeddings)

        # compute similarity probability based on L2 norm
        diff = pairwise_distances(action, embeddings)
        return diff


    def get_best_match(self, action):
        # action = torch.clamp(action, -1, 1)
        if self.fraction < 1 and self.action_dim > 100:
            random_set = np.random.randint(0, self.action_dim, int(self.action_dim * self.fraction))
        else:
            random_set = np.arange(self.action_dim)
        random_set = torch.tensor(random_set, dtype=torch.long)

        diff = self.get_match_scores(action, random_set)
        val, pos = torch.min(diff, dim=1)
        pos = random_set[pos]  #reverse map on the random set.

        # print("-----", action, diff, pos)
        return pos.cpu().data.numpy()[0]


    def get_embedding(self, action):
        # Get the corresponding target embedding
        action = torch.tensor([action], dtype=torch.long) # TODO: check if this step can be moved outside
        action_emb = self.embeddings(action)
        if not self.config.true_embeddings:
            action_emb = F.tanh(action_emb)
        return action_emb

    def forward(self, s1, s2):
        # concatenate the state features and predict the action required to go from state1 to state2
        state_cat = torch.cat([s1, s2], dim=1)
        x = F.tanh(self.fc1(state_cat))
        # x = F.tanh(self.fc2(x))
        return x

    def approx_unsupervised_loss(self, s1, a, s2):
        """
        Only works for single transition updates.
        """
        x = self.forward(s1, s2)

        if self.fraction < 1 and self.action_dim > 100:
            random_set = np.append(a, np.random.randint(0, self.action_dim, int(self.action_dim * self.fraction)))
            pos = self.pos_zero
        else:
            random_set = np.arange(self.action_dim)
            pos = a

        random_set = torch.tensor(random_set, dtype=torch.long)
        diff = - self.get_match_scores(x, random_set)  # Negative euclidean
        loss = F.cross_entropy(diff, pos) + self.config.emb_reg * torch.pow(self.embeddings(random_set), 2).sum()
        return loss

    def unsupervised_loss(self, s1, a, s2):
        x = self.forward(s1, s2)
        random_set = torch.tensor(np.arange(self.action_dim), dtype=torch.long)
        diff = - self.get_match_scores(x, random_set)  # Negative euclidean
        loss = F.cross_entropy(diff, a)/self.norm_const \
               + self.config.emb_reg * torch.pow(self.embeddings(random_set), 2).mean()/self.reduced_action_dim
        return loss


