import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import random
import math
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk


SEED = 42

POPULATION_SIZE = 32
ELITE_COUNT = 6
GENERATIONS = 60

GRID_SIZE = 15
MAX_STEPS = 100

INITIAL_DIFFICULTY = 1.0
MAX_DIFFICULTY = 10.0

MUTATION_RATE = 0.035
MIN_MUTATION_RATE = 0.006

EVAL_EPISODES = 4

POLICY_EPISODES = 2
POLICY_HORIZON = 70

UNSEEN_EPISODES = 12

HIDDEN_1 = 64
HIDDEN_2 = 64

INPUT_SIZE = 18
OUTPUT_SIZE = 4


random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)


class GridWorld:

    ACTIONS = {
        0: (-1, 0),
        1: (1, 0),
        2: (0, -1),
        3: (0, 1),
    }

    def __init__(self, size=GRID_SIZE):

        self.size = size
        self.grid = None
        self.agent = None
        self.goal = None

        self.energy = None
        self.max_energy = None

        self.steps = 0
        self.difficulty = 1.0

        self.moving_goal = False
        self.goal_move_probability = 0.0

        self.moving_obstacles = []

        self.rng = np.random.default_rng()


    def reset(
        self,
        difficulty=1.0,
        seed=None,
        generated_grid=None
    ):

        self.rng = np.random.default_rng(seed)

        self.difficulty = float(
            np.clip(
                difficulty,
                1.0,
                MAX_DIFFICULTY
            )
        )

        if generated_grid is None:

            self.grid = MapGenerator(
                self.size
            ).generate(
                self.difficulty,
                seed=seed
            )

        else:

            self.grid = np.asarray(
                generated_grid,
                dtype=np.int8
            ).copy()

        self.agent = np.array(
            [1, 1],
            dtype=np.int32
        )

        self.goal = np.array(
            [
                self.size - 2,
                self.size - 2
            ],
            dtype=np.int32
        )

        self.moving_goal = (
            self.difficulty >= 6.0
        )

        self.goal_move_probability = (
            min(
                0.25,
                max(
                    0.0,
                    (self.difficulty - 5.0)
                    * 0.035
                )
            )
            if self.moving_goal
            else 0.0
        )

        self.max_energy = max(
            35,
            MAX_STEPS
            - int(
                max(
                    0.0,
                    self.difficulty - 3.0
                ) * 3
            )
        )

        self.energy = float(
            self.max_energy
        )

        self.steps = 0

        self._spawn_moving_obstacles()

        return self.observe()


    def _spawn_moving_obstacles(self):

        self.moving_obstacles = []

        count = max(
            0,
            int(
                (self.difficulty - 2.0)
                * 0.65
            )
        )

        count = min(
            count,
            5
        )

        occupied = {
            tuple(self.agent),
            tuple(self.goal)
        }

        for _ in range(count):

            for _ in range(100):

                r = int(
                    self.rng.integers(
                        2,
                        self.size - 2
                    )
                )

                c = int(
                    self.rng.integers(
                        2,
                        self.size - 2
                    )
                )

                pos = (r, c)

                if self.grid[r, c] != 0:
                    continue

                if pos in occupied:
                    continue

                if (
                    abs(r - 1)
                    + abs(c - 1)
                    < 4
                ):
                    continue

                if (
                    abs(
                        r - (self.size - 2)
                    )
                    + abs(
                        c - (self.size - 2)
                    )
                    < 4
                ):
                    continue

                direction = int(
                    self.rng.integers(
                        0,
                        4
                    )
                )

                self.moving_obstacles.append(
                    {
                        "pos": np.array(
                            [r, c],
                            dtype=np.int32
                        ),
                        "direction": direction
                    }
                )

                occupied.add(pos)

                break


    def is_free(
        self,
        pos,
        include_dynamic=True
    ):

        r = int(pos[0])
        c = int(pos[1])

        if (
            r < 0
            or r >= self.size
            or c < 0
            or c >= self.size
        ):
            return False

        if self.grid[r, c] != 0:
            return False

        if include_dynamic:

            for obstacle in self.moving_obstacles:

                if np.array_equal(
                    obstacle["pos"],
                    [r, c]
                ):
                    return False

        return True


    def _nearest_moving_obstacle(self):

        if not self.moving_obstacles:

            return np.array(
                [
                    0.0,
                    0.0,
                    1.0,
                    0.0
                ],
                dtype=np.float32
            )

        distances = []

        for obstacle in self.moving_obstacles:

            position = obstacle["pos"]

            distance = np.linalg.norm(
                position.astype(float)
                - self.agent.astype(float)
            )

            distances.append(
                (
                    distance,
                    obstacle
                )
            )

        _, obstacle = min(
            distances,
            key=lambda x: x[0]
        )

        delta = (
            obstacle["pos"]
            - self.agent
        )

        direction = (
            obstacle["direction"]
        )

        return np.array(
            [
                delta[0]
                / (self.size - 1),

                delta[1]
                / (self.size - 1),

                direction / 3.0,

                min(
                    1.0,
                    np.linalg.norm(
                        delta
                    )
                    / (self.size - 1)
                )
            ],
            dtype=np.float32
        )


    def observe(self):

        dx = (
            self.goal[0]
            - self.agent[0]
        ) / (self.size - 1)

        dy = (
            self.goal[1]
            - self.agent[1]
        ) / (self.size - 1)

        r, c = self.agent


        def wall(dr, dc):

            return (
                1.0
                if not self.is_free(
                    (
                        r + dr,
                        c + dc
                    ),
                    include_dynamic=False
                )
                else 0.0
            )


        distance = np.linalg.norm(
            self.goal.astype(float)
            - self.agent.astype(float)
        ) / (
            math.sqrt(2)
            * (self.size - 1)
        )

        obstacle_info = (
            self._nearest_moving_obstacle()
        )

        return np.array(
            [
                dx,
                dy,

                wall(-1, 0),
                wall(1, 0),
                wall(0, -1),
                wall(0, 1),

                distance,

                self.energy
                / max(
                    1.0,
                    self.max_energy
                ),

                dx,
                dy,

                obstacle_info[0],
                obstacle_info[1],
                obstacle_info[2],
                obstacle_info[3],

                self.agent[0]
                / (self.size - 1),

                self.agent[1]
                / (self.size - 1),

                self.goal[0]
                / (self.size - 1),

                self.goal[1]
                / (self.size - 1)
            ],
            dtype=np.float32
        )


    def _move_obstacles(self):

        occupied = {
            tuple(self.agent),
            tuple(self.goal)
        }

        for i, obstacle in enumerate(
            self.moving_obstacles
        ):

            direction = (
                obstacle["direction"]
            )

            dr, dc = self.ACTIONS[
                direction
            ]

            candidate = (
                obstacle["pos"]
                + np.array(
                    [dr, dc],
                    dtype=np.int32
                )
            )

            collision = (
                not self.is_free(
                    candidate,
                    include_dynamic=False
                )
                or tuple(candidate)
                in occupied
                or any(
                    j != i
                    and np.array_equal(
                        other["pos"],
                        candidate
                    )
                    for j, other
                    in enumerate(
                        self.moving_obstacles
                    )
                )
            )

            if collision:

                choices = list(
                    range(4)
                )

                self.rng.shuffle(
                    choices
                )

                moved = False

                for new_direction in choices:

                    ndr, ndc = (
                        self.ACTIONS[
                            new_direction
                        ]
                    )

                    candidate = (
                        obstacle["pos"]
                        + np.array(
                            [ndr, ndc],
                            dtype=np.int32
                        )
                    )

                    valid = (
                        self.is_free(
                            candidate,
                            include_dynamic=False
                        )
                        and tuple(candidate)
                        not in occupied
                        and not any(
                            j != i
                            and np.array_equal(
                                other["pos"],
                                candidate
                            )
                            for j, other
                            in enumerate(
                                self.moving_obstacles
                            )
                        )
                    )

                    if valid:

                        obstacle[
                            "direction"
                        ] = new_direction

                        obstacle[
                            "pos"
                        ] = candidate

                        moved = True

                        break

                if not moved:

                    obstacle[
                        "direction"
                    ] = int(
                        self.rng.integers(
                            0,
                            4
                        )
                    )

            else:

                obstacle[
                    "pos"
                ] = candidate

            occupied.add(
                tuple(
                    obstacle["pos"]
                )
            )


    def _move_goal(self):

        if not self.moving_goal:
            return

        if (
            self.rng.random()
            > self.goal_move_probability
        ):
            return

        possible = []

        for dr, dc in (
            self.ACTIONS.values()
        ):

            candidate = (
                self.goal
                + np.array(
                    [dr, dc]
                )
            )

            if (
                self.is_free(
                    candidate,
                    include_dynamic=True
                )
                and not np.array_equal(
                    candidate,
                    self.agent
                )
            ):

                possible.append(
                    candidate
                )

        if possible:

            distances = [
                np.linalg.norm(
                    p.astype(float)
                    - self.agent.astype(float)
                )
                for p in possible
            ]

            self.goal = possible[
                int(
                    np.argmax(
                        distances
                    )
                )
            ]


    def step(self, action):

        action = int(action)

        dr, dc = self.ACTIONS.get(
            action,
            (0, 0)
        )

        old_distance = np.linalg.norm(
            self.goal.astype(float)
            - self.agent.astype(float)
        )

        candidate = (
            self.agent
            + np.array(
                [dr, dc],
                dtype=np.int32
            )
        )

        reward = -0.025

        moved = False
        dynamic_collision = False

        if any(
            np.array_equal(
                obstacle["pos"],
                candidate
            )
            for obstacle
            in self.moving_obstacles
        ):

            reward -= 2.5

            dynamic_collision = True

        elif self.is_free(
            candidate,
            include_dynamic=False
        ):

            self.agent = candidate

            moved = True

            reward += 0.04

        else:

            reward -= 0.12


        new_distance = np.linalg.norm(
            self.goal.astype(float)
            - self.agent.astype(float)
        )

        reward += (
            old_distance
            - new_distance
        ) * 0.22

        self.energy -= 1.0
        self.steps += 1

        self._move_obstacles()

        if any(
            np.array_equal(
                obstacle["pos"],
                self.agent
            )
            for obstacle
            in self.moving_obstacles
        ):

            dynamic_collision = True

            reward -= 4.0


        done = False
        success = False

        if np.array_equal(
            self.agent,
            self.goal
        ):

            reward += 10.0

            done = True
            success = True

        elif dynamic_collision:

            done = True

        elif self.energy <= 0:

            reward -= 3.0

            done = True

        elif self.steps >= MAX_STEPS:

            reward -= 2.0

            done = True


        self._move_goal()

        return (
            self.observe(),
            reward,
            done,
            success,
            moved
        )


class MapGenerator:

    def __init__(
        self,
        size=GRID_SIZE
    ):

        self.size = size


    def generate(
        self,
        difficulty,
        seed=None
    ):

        rng = np.random.default_rng(
            seed
        )

        difficulty = float(
            np.clip(
                difficulty,
                1.0,
                MAX_DIFFICULTY
            )
        )

        density = min(
            0.18,
            0.025
            + difficulty * 0.017
        )

        for _ in range(30):

            grid = np.zeros(
                (
                    self.size,
                    self.size
                ),
                dtype=np.int8
            )

            grid[0, :] = 1
            grid[-1, :] = 1
            grid[:, 0] = 1
            grid[:, -1] = 1

            start = (1, 1)

            goal = (
                self.size - 2,
                self.size - 2
            )

            candidates = [
                (r, c)
                for r in range(
                    1,
                    self.size - 1
                )
                for c in range(
                    1,
                    self.size - 1
                )
            ]

            rng.shuffle(
                candidates
            )

            forbidden = {
                start,
                goal,
                (1, 2),
                (2, 1),
                (
                    self.size - 2,
                    self.size - 3
                ),
                (
                    self.size - 3,
                    self.size - 2
                )
            }

            count = int(
                (self.size - 2) ** 2
                * density
            )

            for cell in candidates[
                :count
            ]:

                if cell not in forbidden:

                    grid[cell] = 1


            segment_count = int(
                max(
                    0.0,
                    difficulty - 3.0
                ) * 0.7
            )

            for _ in range(
                segment_count
            ):

                horizontal = bool(
                    rng.integers(
                        0,
                        2
                    )
                )

                length = int(
                    rng.integers(
                        2,
                        5
                    )
                )

                rr = int(
                    rng.integers(
                        2,
                        self.size - 3
                    )
                )

                cc = int(
                    rng.integers(
                        2,
                        self.size - 3
                    )
                )

                for k in range(length):

                    r = rr + (
                        0
                        if horizontal
                        else k
                    )

                    c = cc + (
                        k
                        if horizontal
                        else 0
                    )

                    if (
                        1 <= r
                        < self.size - 1
                        and
                        1 <= c
                        < self.size - 1
                        and
                        (r, c)
                        not in forbidden
                    ):

                        grid[r, c] = 1


            if self.reachable(
                grid,
                start,
                goal
            ):

                return grid


        grid = np.zeros(
            (
                self.size,
                self.size
            ),
            dtype=np.int8
        )

        grid[0, :] = 1
        grid[-1, :] = 1
        grid[:, 0] = 1
        grid[:, -1] = 1

        return grid


    @staticmethod
    def reachable(
        grid,
        start,
        goal
    ):

        stack = [start]
        visited = {start}

        while stack:

            r, c = stack.pop()

            if (
                r,
                c
            ) == goal:

                return True

            for dr, dc in (
                GridWorld.ACTIONS.values()
            ):

                nr = r + dr
                nc = c + dc

                if (
                    0 <= nr
                    < grid.shape[0]
                    and
                    0 <= nc
                    < grid.shape[1]
                    and
                    grid[nr, nc] == 0
                    and
                    (nr, nc)
                    not in visited
                ):

                    visited.add(
                        (
                            nr,
                            nc
                        )
                    )

                    stack.append(
                        (
                            nr,
                            nc
                        )
                    )

        return False


def build_model():

    return tf.keras.Sequential(
        [
            tf.keras.layers.Input(
                shape=(INPUT_SIZE,)
            ),

            tf.keras.layers.Dense(
                HIDDEN_1,
                activation="relu"
            ),

            tf.keras.layers.Dense(
                HIDDEN_2,
                activation="relu"
            ),

            tf.keras.layers.Dense(
                OUTPUT_SIZE,
                activation="softmax"
            )
        ]
    )


class Agent:

    def __init__(
        self,
        agent_id
    ):

        self.agent_id = agent_id

        self.model = build_model()

        self.fitness = -float("inf")

        self.success_rate = 0.0
        self.average_steps = MAX_STEPS
        self.average_energy = 0.0

        self.policy_loss = 0.0
        self.novelty = 0.0

        self.evolution_score = -float(
            "inf"
        )

        self.face = make_face(
            agent_id
        )

        self.failures = {
            "timeout": 0,
            "energy": 0,
            "collision": 0,
            "navigation": 0
        }


    def act(
        self,
        observation,
        exploration=0.0,
        sample=False
    ):

        obs = np.asarray(
            observation,
            dtype=np.float32
        ).reshape(
            1,
            -1
        )

        probabilities = self.model(
            obs,
            training=False
        )[0]

        if sample:

            action = tf.random.categorical(
                tf.math.log(
                    probabilities[None, :]
                    + 1e-8
                ),
                1
            )[0, 0]

            return int(
                action.numpy()
            )


        if (
            random.random()
            < exploration
        ):

            return random.randrange(
                OUTPUT_SIZE
            )

        return int(
            tf.argmax(
                probabilities
            ).numpy()
        )


def policy_gradient_update(
    agent,
    difficulty,
    episodes=POLICY_EPISODES,
    gamma=0.97,
    learning_rate=0.001
):

    optimizer = tf.keras.optimizers.Adam(
        learning_rate=learning_rate
    )

    losses = []

    for episode in range(
        episodes
    ):

        env = GridWorld()

        obs = env.reset(
            difficulty=difficulty,
            seed=(
                700000
                + agent.agent_id * 1009
                + episode * 53
            )
        )

        observations = []
        actions = []
        rewards = []

        for _ in range(
            POLICY_HORIZON
        ):

            observations.append(
                obs.copy()
            )

            action = agent.act(
                obs,
                sample=True
            )

            next_obs, reward, done, _, _ = (
                env.step(action)
            )

            actions.append(action)
            rewards.append(
                float(reward)
            )

            obs = next_obs

            if done:
                break


        if not rewards:
            continue


        returns = []

        running = 0.0

        for reward in reversed(
            rewards
        ):

            running = (
                reward
                + gamma * running
            )

            returns.append(
                running
            )

        returns.reverse()

        returns = np.asarray(
            returns,
            dtype=np.float32
        )

        if returns.std() > 1e-6:

            returns = (
                returns
                - returns.mean()
            ) / (
                returns.std()
                + 1e-6
            )


        obs_tensor = tf.convert_to_tensor(
            np.asarray(
                observations
            ),
            dtype=tf.float32
        )

        action_tensor = tf.convert_to_tensor(
            actions,
            dtype=tf.int32
        )

        return_tensor = tf.convert_to_tensor(
            returns,
            dtype=tf.float32
        )


        with tf.GradientTape() as tape:

            probs = agent.model(
                obs_tensor,
                training=True
            )

            indices = tf.stack(
                [
                    tf.range(
                        tf.shape(
                            action_tensor
                        )[0]
                    ),
                    action_tensor
                ],
                axis=1
            )

            selected = tf.gather_nd(
                probs,
                indices
            )

            log_probs = tf.math.log(
                selected
                + 1e-8
            )

            entropy = -tf.reduce_mean(
                tf.reduce_sum(
                    probs
                    * tf.math.log(
                        probs
                        + 1e-8
                    ),
                    axis=1
                )
            )

            loss = (
                -tf.reduce_mean(
                    log_probs
                    * return_tensor
                )
                - 0.01 * entropy
            )


        gradients = tape.gradient(
            loss,
            agent.model.trainable_variables
        )

        clipped = [
            None
            if gradient is None
            else tf.clip_by_norm(
                gradient,
                1.0
            )
            for gradient in gradients
        ]

        optimizer.apply_gradients(
            zip(
                clipped,
                agent.model.trainable_variables
            )
        )

        losses.append(
            float(
                loss.numpy()
            )
        )


    agent.policy_loss = (
        float(
            np.mean(losses)
        )
        if losses
        else 0.0
    )

    return agent.policy_loss


def evaluate_agent(
    agent,
    difficulty,
    episodes=EVAL_EPISODES,
    seed_base=None
):

    rewards = []
    successes = []
    steps_list = []
    energies = []

    failures = {
        "timeout": 0,
        "energy": 0,
        "collision": 0,
        "navigation": 0
    }


    for episode in range(
        episodes
    ):

        env = GridWorld()

        seed = (
            None
            if seed_base is None
            else seed_base
            + episode * 997
        )

        obs = env.reset(
            difficulty=difficulty,
            seed=seed
        )

        total_reward = 0.0
        success = False


        for _ in range(
            MAX_STEPS
        ):

            action = agent.act(
                obs,
                exploration=0.015
            )

            (
                obs,
                reward,
                done,
                success,
                _
            ) = env.step(action)

            total_reward += reward

            if done:
                break


        rewards.append(
            total_reward
        )

        successes.append(
            float(success)
        )

        steps_list.append(
            env.steps
        )

        energies.append(
            env.energy
        )


        if success:

            pass

        elif any(
            np.array_equal(
                obstacle["pos"],
                env.agent
            )
            for obstacle
            in env.moving_obstacles
        ):

            failures[
                "collision"
            ] += 1

        elif env.energy <= 0:

            failures[
                "energy"
            ] += 1

        elif env.steps >= MAX_STEPS:

            failures[
                "timeout"
            ] += 1

        else:

            failures[
                "navigation"
            ] += 1


    avg_reward = float(
        np.mean(rewards)
    )

    success_rate = float(
        np.mean(successes)
    )

    avg_steps = float(
        np.mean(steps_list)
    )

    avg_energy = float(
        np.mean(energies)
    )


    fitness = (
        avg_reward
        + success_rate * 8.0
        + max(
            0.0,
            (
                MAX_STEPS
                - avg_steps
            )
            / MAX_STEPS
        )
        * 1.5
    )


    agent.fitness = fitness
    agent.success_rate = success_rate
    agent.average_steps = avg_steps
    agent.average_energy = avg_energy
    agent.failures = failures


    return {
        "fitness": fitness,
        "reward": avg_reward,
        "success_rate": success_rate,
        "steps": avg_steps,
        "energy": avg_energy,
        "failures": failures
    }


def behavioral_signature(
    agent,
    difficulty,
    samples=10
):

    signature = []

    for i in range(
        samples
    ):

        env = GridWorld()

        obs = env.reset(
            difficulty=difficulty,
            seed=(
                500000
                + agent.agent_id * 1009
                + i * 31
            )
        )


        for _ in range(60):

            action = agent.act(
                obs
            )

            (
                obs,
                _,
                done,
                _,
                _
            ) = env.step(
                action
            )

            if done:
                break


        signature.extend(
            [
                env.agent[0]
                / (env.size - 1),

                env.agent[1]
                / (env.size - 1),

                env.goal[0]
                / (env.size - 1),

                env.goal[1]
                / (env.size - 1)
            ]
        )


    return np.asarray(
        signature,
        dtype=np.float32
    )


def novelty_score(
    signature,
    archive
):

    if not archive:
        return 0.0

    distances = [
        float(
            np.linalg.norm(
                signature
                - old
            )
        )
        for old in archive
    ]

    distances.sort()

    return float(
        np.mean(
            distances[
                :min(
                    5,
                    len(distances)
                )
            ]
        )
    )


def crossover_weights(
    parent_a,
    parent_b,
    rng
):

    weights_a = (
        parent_a.model.get_weights()
    )

    weights_b = (
        parent_b.model.get_weights()
    )

    child = []

    for wa, wb in zip(
        weights_a,
        weights_b
    ):

        mask = (
            rng.random(
                wa.shape
            )
            < 0.5
        )

        child.append(
            np.where(
                mask,
                wa,
                wb
            ).astype(
                np.float32
            )
        )

    return child


def mutate_weights(
    weights,
    mutation_rate,
    rng
):

    result = []

    for weight in weights:

        noise = rng.normal(
            0.0,
            mutation_rate,
            size=weight.shape
        ).astype(
            np.float32
        )

        macro_mask = (
            rng.random(
                weight.shape
            )
            < 0.008
        )

        if np.any(
            macro_mask
        ):

            macro_noise = rng.normal(
                0.0,
                mutation_rate * 4.0,
                size=weight.shape
            ).astype(
                np.float32
            )

            noise = np.where(
                macro_mask,
                macro_noise,
                noise
            )

        result.append(
            (
                weight
                + noise
            ).astype(
                np.float32
            )
        )

    return result


def adapt_difficulty(
    current,
    population
):

    best = max(
        agent.success_rate
        for agent in population
    )

    average = float(
        np.mean(
            [
                agent.success_rate
                for agent in population
            ]
        )
    )


    if (
        best >= 0.90
        and average >= 0.55
    ):

        current += 0.35

    elif average <= 0.15:

        current -= 0.20


    return float(
        np.clip(
            current,
            INITIAL_DIFFICULTY,
            MAX_DIFFICULTY
        )
    )


def update_mutation(
    rate,
    best_success,
    average_success,
    diversity
):

    if diversity < 0.70:

        rate *= 1.12

    elif diversity > 1.54:

        rate *= 0.94


    if (
        best_success >= 0.92
        and average_success >= 0.65
    ):

        rate *= 0.96

    elif average_success < 0.20:

        rate *= 1.08


    return float(
        np.clip(
            rate,
            MIN_MUTATION_RATE,
            0.12
        )
    )


FACE_POOL = list(
    "@.#%&*+xo^v<>"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
)


def make_face(
    agent_index
):

    return FACE_POOL[
        agent_index
        % len(FACE_POOL)
    ]


def diagnose_population(
    population
):

    counts = {
        key: sum(
            agent.failures[key]
            for agent in population
        )
        for key in population[0].failures
    }

    total = max(
        1,
        sum(
            counts.values()
        )
    )

    ratios = {
        key: value / total
        for key, value in counts.items()
    }

    dominant = (
        max(
            ratios,
            key=ratios.get
        )
        if sum(counts.values())
        else "none"
    )

    return ratios, dominant


def render_population(
    population,
    cols=8
):

    ranked = sorted(
        population,
        key=lambda agent:
            agent.fitness,
        reverse=True
    )

    print()
    print("POPULATION")
    print("-" * 100)

    for i in range(
        0,
        len(ranked),
        cols
    ):

        cells = []

        for agent in ranked[
            i:i + cols
        ]:

            status = (
                "★"
                if agent.success_rate
                >= 0.9
                else "·"
            )

            cells.append(
                f"({agent.face})"
                f"{agent.success_rate * 100:3.0f}%"
                f"{status}"
            )

        print(
            " ".join(
                f"{cell:10s}"
                for cell in cells
            )
        )

    print("-" * 100)


def test_generalization(
    agent,
    difficulty
):

    results = []

    generator = MapGenerator()

    for episode in range(
        UNSEEN_EPISODES
    ):

        grid = generator.generate(
            difficulty,
            seed=(
                100000
                + episode * 1337
            )
        )

        env = GridWorld()

        obs = env.reset(
            difficulty=difficulty,
            seed=(
                200000
                + episode * 17
            ),
            generated_grid=grid
        )

        total_reward = 0.0
        success = False

        for _ in range(
            MAX_STEPS
        ):

            action = agent.act(
                obs
            )

            (
                obs,
                reward,
                done,
                success,
                _
            ) = env.step(
                action
            )

            total_reward += reward

            if done:
                break


        results.append(
            {
                "episode": episode + 1,
                "success": int(
                    success
                ),
                "reward": total_reward,
                "steps": env.steps
            }
        )


    df = pd.DataFrame(
        results
    )

    return {
        "success_rate": float(
            df["success"].mean()
        ),
        "average_reward": float(
            df["reward"].mean()
        ),
        "average_steps": float(
            df["steps"].mean()
        ),
        "episodes": df
    }


class SimulationViewer:

    def __init__(
        self,
        champion,
        difficulty
    ):

        self.champion = champion
        self.difficulty = difficulty

        self.generator = (
            MapGenerator()
        )

        self.root = tk.Tk()

        self.root.title(
            "EVO-1 | Live Neural Agent"
        )

        self.root.geometry(
            "760x760"
        )

        self.running = True
        self.paused = False

        self.episode = 0
        self.successes = 0
        self.failures = 0

        self.cell = 42


        top = ttk.Frame(
            self.root
        )

        top.pack(
            fill=tk.X,
            padx=12,
            pady=8
        )


        self.status = ttk.Label(
            top,
            text="Initializing..."
        )

        self.status.pack(
            side=tk.LEFT
        )


        ttk.Button(
            top,
            text="Pause / Resume",
            command=self.toggle_pause
        ).pack(
            side=tk.RIGHT
        )


        ttk.Button(
            top,
            text="New Map",
            command=self.new_episode
        ).pack(
            side=tk.RIGHT,
            padx=6
        )


        self.canvas = tk.Canvas(
            self.root,
            width=650,
            height=650,
            highlightthickness=0
        )

        self.canvas.pack(
            pady=6
        )


        self.info = ttk.Label(
            self.root,
            text="",
            font=(
                "Consolas",
                11
            )
        )

        self.info.pack(
            pady=8
        )


        self.new_episode()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

        self.root.after(
            55,
            self.tick
        )

        self.root.mainloop()


    def new_episode(self):

        self.episode += 1

        seed = (
            900000
            + self.episode * 173
        )

        grid = self.generator.generate(
            self.difficulty,
            seed=seed
        )

        self.env = GridWorld()

        self.obs = self.env.reset(
            difficulty=self.difficulty,
            seed=seed + 1,
            generated_grid=grid
        )

        self.path = {
            tuple(
                self.env.agent
            )
        }

        self.dead = False
        self.last_success = False
        self.last_reward = 0.0


    def toggle_pause(self):

        self.paused = (
            not self.paused
        )


    def close(self):

        self.running = False

        self.root.destroy()


    def tick(self):

        if not self.running:
            return


        if not self.paused:

            if self.dead:

                self.new_episode()

            else:

                action = self.champion.act(
                    self.obs,
                    exploration=0.0
                )

                (
                    self.obs,
                    reward,
                    done,
                    success,
                    _
                ) = self.env.step(
                    action
                )

                self.last_reward = reward

                self.path.add(
                    tuple(
                        self.env.agent
                    )
                )


                if done:

                    self.dead = True

                    self.last_success = (
                        success
                    )

                    if success:
                        self.successes += 1
                    else:
                        self.failures += 1


        self.draw()

        self.root.after(
            55,
            self.tick
        )


    def draw(self):

        self.canvas.delete(
            "all"
        )

        offset_x = 8
        offset_y = 8


        for r in range(
            self.env.size
        ):

            for c in range(
                self.env.size
            ):

                x1 = (
                    offset_x
                    + c * self.cell
                )

                y1 = (
                    offset_y
                    + r * self.cell
                )

                x2 = (
                    x1
                    + self.cell
                )

                y2 = (
                    y1
                    + self.cell
                )


                if (
                    self.env.grid[
                        r,
                        c
                    ]
                    == 1
                ):

                    fill = "#222222"

                elif (
                    r,
                    c
                ) in self.path:

                    fill = "#e8e8e8"

                else:

                    fill = "white"


                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline="#cccccc"
                )


        gr, gc = map(
            int,
            self.env.goal
        )

        gx = (
            offset_x
            + gc * self.cell
            + self.cell / 2
        )

        gy = (
            offset_y
            + gr * self.cell
            + self.cell / 2
        )


        self.canvas.create_text(
            gx,
            gy,
            text="★",
            font=(
                "Arial",
                24,
                "bold"
            )
        )


        for obstacle in (
            self.env.moving_obstacles
        ):

            rr, cc = map(
                int,
                obstacle["pos"]
            )

            ox = (
                offset_x
                + cc * self.cell
                + self.cell / 2
            )

            oy = (
                offset_y
                + rr * self.cell
                + self.cell / 2
            )


            self.canvas.create_oval(
                ox - 14,
                oy - 14,
                ox + 14,
                oy + 14,
                fill="#777777",
                outline="#111111",
                width=2
            )


            self.canvas.create_text(
                ox,
                oy,
                text="◆",
                font=(
                    "Arial",
                    14,
                    "bold"
                )
            )


        ar, ac = map(
            int,
            self.env.agent
        )

        ax = (
            offset_x
            + ac * self.cell
            + self.cell / 2
        )

        ay = (
            offset_y
            + ar * self.cell
            + self.cell / 2
        )


        self.canvas.create_oval(
            ax - 15,
            ay - 15,
            ax + 15,
            ay + 15,
            outline="#111111",
            width=3
        )


        self.canvas.create_text(
            ax,
            ay,
            text=f"({self.champion.face})",
            font=(
                "Consolas",
                11,
                "bold"
            )
        )


        if self.paused:

            state = "PAUSED"

        elif self.dead:

            state = (
                "SUCCESS"
                if self.last_success
                else "FAILED"
            )

        else:

            state = "RUNNING"


        self.status.config(
            text=(
                f"EVO-1 | {state} | "
                f"episode {self.episode} | "
                f"difficulty "
                f"{self.difficulty:.2f}"
            )
        )


        self.info.config(
            text=(
                f"agent=({self.champion.face})    "
                f"step={self.env.steps:03d}    "
                f"energy={self.env.energy:5.1f}    "
                f"reward={self.last_reward:6.2f}    "
                f"success={self.successes}    "
                f"fail={self.failures}"
            )
        )


def plot_results(
    history_df
):

    plt.figure(
        figsize=(11, 5)
    )

    plt.plot(
        history_df["generation"],
        history_df["best_fitness"],
        label="Best fitness"
    )

    plt.plot(
        history_df["generation"],
        history_df["average_fitness"],
        label="Average fitness"
    )

    plt.xlabel(
        "Generation"
    )

    plt.ylabel(
        "Fitness"
    )

    plt.title(
        "EVO-1 Evolution"
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.show()


    plt.figure(
        figsize=(11, 5)
    )

    plt.plot(
        history_df["generation"],
        history_df["best_success_rate"]
        * 100,
        label="Best success"
    )

    plt.plot(
        history_df["generation"],
        history_df["average_success_rate"]
        * 100,
        label="Average success"
    )

    plt.xlabel(
        "Generation"
    )

    plt.ylabel(
        "Success (%)"
    )

    plt.title(
        "Policy Improvement"
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.show()


    plt.figure(
        figsize=(11, 5)
    )

    plt.plot(
        history_df["generation"],
        history_df["behavioral_diversity"],
        label="Behavioral diversity"
    )

    plt.plot(
        history_df["generation"],
        history_df["mutation_rate"],
        label="Mutation rate"
    )

    plt.xlabel(
        "Generation"
    )

    plt.ylabel(
        "Value"
    )

    plt.title(
        "Evolutionary Diversity"
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.show()


    plt.figure(
        figsize=(11, 5)
    )

    plt.plot(
        history_df["generation"],
        history_df["difficulty"],
        label="Difficulty"
    )

    plt.plot(
        history_df["generation"],
        history_df["best_success_rate"],
        label="Best success rate"
    )

    plt.xlabel(
        "Generation"
    )

    plt.ylabel(
        "Value"
    )

    plt.title(
        "Adaptive Curriculum"
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.show()


def train():

    population = [
        Agent(i)
        for i in range(
            POPULATION_SIZE
        )
    ]


    difficulty = (
        INITIAL_DIFFICULTY
    )

    mutation_rate = (
        MUTATION_RATE
    )

    history = []

    archive = []

    global_best_weights = None

    global_best_fitness = -float(
        "inf"
    )

    global_best_face = None


    for generation in range(
        1,
        GENERATIONS + 1
    ):

        for agent in population:

            policy_gradient_update(
                agent,
                difficulty=difficulty,
                episodes=POLICY_EPISODES,
                gamma=0.97,
                learning_rate=0.001
            )


        for agent in population:

            evaluate_agent(
                agent,
                difficulty=difficulty,
                episodes=EVAL_EPISODES,
                seed_base=(
                    SEED
                    + generation * 10000
                    + agent.agent_id * 101
                )
            )


        population.sort(
            key=lambda agent:
                agent.fitness,
            reverse=True
        )


        signatures = [
            behavioral_signature(
                agent,
                difficulty
            )
            for agent in population
        ]


        distances = []

        for i in range(
            len(signatures)
        ):

            for j in range(
                i + 1,
                len(signatures)
            ):

                distances.append(
                    float(
                        np.linalg.norm(
                            signatures[i]
                            - signatures[j]
                        )
                    )
                )


        diversity = (
            float(
                np.mean(
                    distances
                )
            )
            if distances
            else 0.0
        )


        for agent, signature in zip(
            population,
            signatures
        ):

            agent.novelty = (
                novelty_score(
                    signature,
                    archive
                )
            )


        archive.extend(
            signatures
        )


        if len(archive) > 120:

            archive = archive[
                -120:
            ]


        for agent in population:

            agent.evolution_score = (
                agent.fitness
                + min(
                    agent.novelty,
                    20.0
                ) * 0.18
            )


        population.sort(
            key=lambda agent:
                agent.evolution_score,
            reverse=True
        )


        best = population[0]


        avg_fitness = float(
            np.mean(
                [
                    agent.fitness
                    for agent in population
                ]
            )
        )


        avg_success = float(
            np.mean(
                [
                    agent.success_rate
                    for agent in population
                ]
            )
        )


        ratios, dominant = (
            diagnose_population(
                population
            )
        )


        if (
            best.fitness
            > global_best_fitness
        ):

            global_best_fitness = (
                best.fitness
            )

            global_best_weights = [
                weight.copy()
                for weight
                in best.model.get_weights()
            ]

            global_best_face = (
                best.face
            )


        history.append(
            {
                "generation": generation,
                "difficulty": difficulty,
                "best_fitness": best.fitness,
                "average_fitness": avg_fitness,
                "best_success_rate":
                    best.success_rate,
                "average_success_rate":
                    avg_success,
                "best_steps":
                    best.average_steps,
                "mutation_rate":
                    mutation_rate,
                "behavioral_diversity":
                    diversity,
                "best_novelty":
                    best.novelty,
                "policy_loss":
                    best.policy_loss,
                "failure_timeout":
                    ratios["timeout"],
                "failure_energy":
                    ratios["energy"],
                "failure_collision":
                    ratios["collision"],
                "failure_navigation":
                    ratios["navigation"]
            }
        )


        print(
            f"[GEN {generation:03d}] "
            f"champion=({best.face}) "
            f"fitness={best.fitness:7.2f} | "
            f"avg={avg_fitness:7.2f} | "
            f"success="
            f"{best.success_rate * 100:5.1f}% | "
            f"div={diversity:6.2f} | "
            f"nov={best.novelty:6.2f} | "
            f"loss={best.policy_loss:7.3f} | "
            f"diff={difficulty:4.2f} | "
            f"mut={mutation_rate:.4f} | "
            f"weakness={dominant}"
        )


        if (
            generation == 1
            or generation % 5 == 0
        ):

            render_population(
                population
            )


        difficulty = (
            adapt_difficulty(
                difficulty,
                population
            )
        )


        mutation_rate = (
            update_mutation(
                mutation_rate,
                best.success_rate,
                avg_success,
                diversity
            )
        )


        elites = population[
            :ELITE_COUNT
        ]

        new_population = list(
            elites
        )

        rng = np.random.default_rng(
            SEED
            + generation * 991
        )

        child_id = (
            ELITE_COUNT
        )


        while len(
            new_population
        ) < POPULATION_SIZE:

            parent_a = random.choice(
                elites
            )

            parent_b = random.choice(
                elites
            )


            if len(elites) > 1:

                while (
                    parent_b
                    is parent_a
                ):

                    parent_b = (
                        random.choice(
                            elites
                        )
                    )


            child = Agent(
                child_id
            )


            crossed = (
                crossover_weights(
                    parent_a,
                    parent_b,
                    rng
                )
            )


            mutated = (
                mutate_weights(
                    crossed,
                    mutation_rate,
                    rng
                )
            )


            child.model.set_weights(
                mutated
            )

            new_population.append(
                child
            )

            child_id += 1


        population = (
            new_population
        )


    for agent in population:

        evaluate_agent(
            agent,
            difficulty=difficulty,
            episodes=EVAL_EPISODES,
            seed_base=(
                777000
                + agent.agent_id * 31
            )
        )


    champion = Agent(0)

    champion.face = (
        global_best_face
        if global_best_face
        is not None
        else "@"
    )


    if (
        global_best_weights
        is not None
    ):

        champion.model.set_weights(
            global_best_weights
        )


    evaluate_agent(
        champion,
        difficulty=difficulty,
        episodes=EVAL_EPISODES,
        seed_base=888000
    )


    unseen = (
        test_generalization(
            champion,
            difficulty
        )
    )


    history_df = pd.DataFrame(
        history
    )


    history_df.to_csv(
        "evo_history.csv",
        index=False
    )


    unseen[
        "episodes"
    ].to_csv(
        "evo_unseen_results.csv",
        index=False
    )


    print()
    print("=" * 100)
    print(
        "EVOLUTION COMPLETE"
    )
    print("=" * 100)

    print(
        f"Generations       : "
        f"{GENERATIONS}"
    )

    print(
        f"Population        : "
        f"{POPULATION_SIZE}"
    )

    print(
        f"Final difficulty  : "
        f"{difficulty:.2f}"
    )

    print(
        f"Champion          : "
        f"({champion.face})"
    )

    print(
        f"Fitness           : "
        f"{champion.fitness:.3f}"
    )

    print(
        f"Success           : "
        f"{champion.success_rate * 100:.2f}%"
    )

    print(
        f"Unseen success    : "
        f"{unseen['success_rate'] * 100:.2f}%"
    )

    print()
    print(
        "Saved "
        "evo_history.csv"
    )

    print(
        "Saved "
        "evo_unseen_results.csv"
    )

    print()
    print(
        "Launching live simulation..."
    )


    render_population(
        population
    )


    SimulationViewer(
        champion,
        difficulty
    )


    plot_results(
        history_df
    )


    return (
        champion,
        history_df,
        unseen
    )


if __name__ == "__main__":

    try:

        train()

    except KeyboardInterrupt:

        print(
            "\nTraining interrupted."
        )

    except Exception as exc:

        print(
            "\nEVO-1 stopped:"
        )

        print(
            type(exc).__name__,
            ":",
            exc
        )

        print(
            "\nInstall:"
        )

        print(
            "pip install tensorflow "
            "numpy pandas matplotlib"
        )
