#!~miniconda3/envs/pytorch/bin python
# from __future__ import print_function

# Dynamic cython compilation
import pyximport; pyximport.install()
# from memory_profiler import profile

import numpy as np
import Src.Utils.utils as utils
from Src.parser import Parser
from Src.parser import Parser
from Src.config import Config
from time import time



class Solver:
    def __init__(self, config):
        # Initialize the required variables

        self.config = config
        self.env = self.config.env
        self.state_dim = np.shape(self.env.reset())[0]
        #mine
        try:
            if len(self.env.action_space.shape) > 0:
                self.action_dim = self.env.action_space.shape[0]
        except:
            self.action_dim = self.env.action_space.n
        #
        print("Actions space: {} :: State space: {}".format(self.action_dim, self.state_dim))

        ##mine
        self.model = config.algo.embed_ActorCritic(config=config)

    def eval(self, episodes=1):
        # Evaluate the model
        rewards = []
        steps = []
        for episode in range(episodes):
            trajectory = []
            state = np.float32(self.env.reset())
            total_r, step = 0, 0
            done = False
            while not done:
                # if step%1 == 0:
                #     self.env.render()  # Display environment GUI

                action, dist, extra_sampled_actions = self.model.get_action(state, explore=0)
                ## mine for continuous mountatin car:
                ## new_state, reward, done, info = self.env.step(np.reshape(action,1))
                new_state, reward, done, info = self.env.step(action_index=action, extra_sampled_actions = extra_sampled_actions)
                state = new_state

                trajectory.append((action, reward))
                total_r += reward
                step += 1

            rewards.append(total_r)
            steps.append(step)

            print(trajectory)
            print(info)
        return rewards, steps

    def train(self):
        # Learn the model on the environment
        returns = []
        ckpt = self.config.save_after
        rewards, rm, start_ep = [], 0, 0
        if self.config.restore:
            returns = list(np.load(self.config.paths['results']+"rewards.npy"))
            rm = returns[-1]
            start_ep = np.size(returns)
            print(start_ep)

        steps = 0
        t0 = time()
        schedule = utils.Linear_schedule(max_len=self.config.max_episodes)
        for episode in range(start_ep, self.config.max_episodes):
            # Reset both environment and model before a new episode
            state = self.env.reset()
            self.model.reset()

            exp = schedule.get(episode)
            step, total_r = 0, 0
            done = False
            while not done:
                # self.env.render()
                action, extra_info, extra_sampled_actions = self.model.get_action(state, explore=exp)
                # print(action, dist.data.numpy())
                # action = np.clip(action, self.model.action_low, self.model.action_high)  # !! Never do this - it updates the policy at action which was not sampled
                
                ## mine: for continuous mountatin car
                ## new_state, reward, done, info = self.env.step(action=np.reshape(action,1))
                
                ## mine: malware_v0 has action_index
                if self.config.env.spec.id != 'malware-v0':
                    new_state, reward, done, info = self.env.step(action=action)
                else:
                    new_state, reward, done, info = self.env.step(action_index=action, extra_sampled_actions = extra_sampled_actions)
                self.model.update(state, action, extra_info, reward, new_state, done)
                state = new_state

                # Tracking intra-episode progress
                total_r += reward
                step += 1
                if step > self.config.max_steps:
                    break

            # track inter-episode progress
            # returns.append(total_r)
            steps += step
            rm = 0.99*rm + 0.01*total_r

            if episode%ckpt == 0 or episode == self.config.max_episodes-1:
                returns.append(total_r)
                # rewards.append(rm)
                print("{} :: Rewards {:.3f} :: steps: {:.2f} :: Time: {:.3f}({:.5f}/step) :: Entropy : {:.3f} :: Grads : {}".
                      format(episode, rm, steps/ckpt, (time() - t0)/ckpt, (time() - t0)/steps, self.model.entropy, self.model.get_grads()))

                self.model.save()
                utils.save_plots(returns, config=self.config)
                # utils.save_plots(rewards, config=self.config)

                t0 = time()
                steps = 0

            # gc.collect()  #Makes code slow!

    def random_eval(self, episodes=1):
        # Evaluate the model
        rewards = []
        steps = []
        for episode in range(episodes):
            trajectory = []
            state = np.float32(self.env.reset())
            total_r, step = 0, 0
            done = False
            while not done:
                # action = np.random.randint(self.action_dim)

                action, dist = self.model.get_action(state, explore=0)
                new_state, reward, done, info = self.env.step(action)
                state = new_state

                # trajectory.append((action, reward))
                total_r += reward
                step += 1

            rewards.append(total_r)
            steps.append(step)

        print("Average rewards: ", np.mean(rewards))
        exit()

# @profile
def main(train=True, inc=-1, hyper=-1, base=-1):
    t = time()
    args = Parser().get_parser().parse_args()

    if inc >= 0 and hyper >= 0 and base >= 0:
        args.inc = inc
        args.hyper = hyper
        args.base = base

    config = Config(args)
    solver = Solver(config=config)

    # solver.random_eval(episodes=1000)
    # Training mode
    if train:
        solver.train()

    # Evaluation mode
    solver.eval(10)

    print(time()-t)

if __name__== "__main__":
        # import cProfile
        # cProfile.run('main()', sort='cumtime')
        main(train=True)

