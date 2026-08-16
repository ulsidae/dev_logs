# 🎯 Bullet Hell Dodge Experiment

> A small screen-based game-agent experiment built with computer vision, motion tracking, and heuristic risk evaluation.
>
> Tested with **Touhou 18: Unconnected Marketeers**.

I built this as a small toy project after finishing my TOEFL preparation.

The goal wasn't to build a production-ready game bot or a machine-learning system. I just wanted to see how far a relatively simple program could get by **watching a bullet-hell game through pixels, estimating what was happening on screen, predicting incoming bullets, and making movement decisions in real time**.

It was intentionally kept small and experimental, and is no longer under active development.

---

## 🧪 Experiment Overview

The project uses screen capture and computer vision to build a simple real-time bullet-dodging agent.

The basic pipeline looks like this:

```
Game Screen
    ↓
Screen Capture
    ↓
Player Detection
    ↓
Bullet Detection
    ↓
Bullet Tracking
    ↓
Velocity Estimation
    ↓
Trajectory Prediction
    ↓
Risk Evaluation
    ↓
Movement Decision
    ↓
Keyboard Input
```

Rather than reading the game's internal state or memory, the agent treats the game as a visual input and works entirely from the captured screen.

In that sense, it's closer to a simple **vision-based game agent** than a traditional bot that directly interacts with the game's internal data.

---

## 🎮 Test Environment

The system was primarily tested with:

* **Game:** Touhou 18: Unconnected Marketeers
* **Platform:** Windows 10
* **Language:** Python
* **Input:** PyDirectInput
* **Computer Vision:** OpenCV
* **Screen Capture:** MSS

The experiment was mainly tuned to survive the early game and attempt a first-stage clear rather than play through the entire game.

---

## 🤖 How It Works

### Player Detection

The agent searches for the player near its previously detected position instead of scanning the entire screen every frame.

This provides a lightweight form of local tracking.

The detected position is also smoothed over time to reduce jitter caused by visual noise.

---

### Bullet Detection

Bright objects are extracted from each frame using HSV-based thresholding.

Potential bullets are filtered by:

* Contour area
* Bounding-box size
* Screen boundaries
* Distance from the player

The result is a simplified representation of the current bullet field.

---

### Bullet Tracking

Detected bullets are matched with objects from the previous frame using nearest-neighbor matching.

For each tracked bullet, the agent maintains:

```
position
velocity
radius
track age
```

Velocity estimates are smoothed between frames to reduce instability.

It's intentionally simple, so tracking can become unreliable when many bullets are close together.

---

### Trajectory Prediction

Once a bullet has an estimated velocity, its future position is approximated using a simple linear model:

```
future_position = current_position + velocity × prediction_steps
```

Instead of reacting only to where a bullet is right now, the agent checks several future positions to estimate where the bullet is heading.

This allows it to react to bullets that are still relatively far away but moving toward the player.

---

### Risk Evaluation

The agent generates a set of candidate positions around the player and assigns each one a risk score.

The score takes into account things like:

* Predicted bullet collisions
* Distance from nearby bullets
* Bullet movement direction
* Distance from the play-field boundaries
* Distance from the preferred position
* Amount of movement required

The lowest-risk candidate becomes the next movement target.

In simplified terms:

> **Observe → Predict → Evaluate → Move**

---

## 🧠 Decision Model

This experiment does **not** use a trained neural network or reinforcement learning.

Instead, it relies on a lightweight heuristic decision system.

The agent combines:

* Computer vision
* Local object tracking
* Velocity estimation
* Linear trajectory prediction
* Heuristic risk scoring
* Real-time keyboard control

So rather than calling it a machine-learning model, it's more accurate to describe it as a **rule-based game-agent experiment**.

The idea was to explore the basic building blocks of a game-playing agent without introducing a full training pipeline.

---

## 🏗️ Technical Stack

### Python

The primary implementation language.

### OpenCV

Used for:

* Image processing
* HSV thresholding
* Morphological filtering
* Contour detection
* Object localization

### MSS

Used for real-time screen capture.

### NumPy

Used for image and numerical processing.

### PyDirectInput

Used to send keyboard input to the game.

### PyGetWindow

Used to locate the game window and determine the capture region dynamically.

### Keyboard

Used for global hotkeys to control the experiment.

---

## 🎛️ Controls

```
F6 → Start
F7 → Stop
F2 → Exit
```

While running, the agent automatically holds the game's action key and controls movement through keyboard input.

All controlled keys are released when the experiment stops.

---

## 🔬 Why I Built This

This started as a **toy project to learn more about AI and game-agent development**.

The question was simple:

> **How far can a program get if it only sees the game through pixels?**

Rather than starting with a neural network, I built a small perception-and-control loop:

1. Capture the screen.
2. Locate the player.
3. Detect bullets.
4. Track their movement.
5. Estimate their velocity.
6. Predict their future positions.
7. Evaluate which positions are dangerous.
8. Move toward a safer position.

The project was mainly an exercise in turning an abstract game-agent idea into something that actually runs in real time.

---

## 📦 Project Status

This project is **complete as an experiment and is no longer actively maintained**.

Development stopped once the initial experiment had served its purpose.

The code was written quickly and iterated on experimentally rather than designed as a polished software package.

Some experimental variables and logic remain from earlier iterations, and the source code contains relatively little inline documentation.

The repository is kept as a record of the experiment and as a small example of:

* Computer vision
* Real-time object tracking
* Motion prediction
* Heuristic planning
* Automated game control

---

## 📝 About the Code

This was a short-lived toy project I built after finishing my TOEFL preparation.

The priority was experimentation and iteration rather than maintainability.

The implementation went through several quick iterations while I experimented with different detection, prediction, and movement heuristics.

As a result, the final code is intentionally lightweight and isn't heavily documented.

It's best thought of as an **experiment log in code form**, rather than a reusable framework.

---

## 🚧 Limitations

There are several obvious limitations in the current implementation.

### Visual Detection

The system relies heavily on brightness, color, and shape-based detection.

As a result, visual effects and other bright objects can sometimes be mistaken for bullets.

Player detection is also based on visual heuristics rather than a trained detector.

### Tracking

Bullet tracking uses nearest-neighbor matching between consecutive frames.

Dense bullet patterns can cause incorrect associations or tracks to switch between objects.

### Prediction

The prediction model assumes approximately linear motion.

It does not account for:

* Curved trajectories
* Acceleration
* Complex movement patterns
* Game-specific spawning behavior

### Decision Making

The risk model is entirely heuristic.

It doesn't learn from previous attempts or improve through experience.

### Game Understanding

The agent has no semantic understanding of the game.

It doesn't know:

* Which attack pattern is currently active
* Which stage or phase the game is in
* Which objects are important
* Whether its attacks are actually successful

It simply reacts to what it can observe from the captured screen.

---

## 🔮 Possible Future Directions

If I were to continue the experiment, some interesting directions would be:

* More robust player and bullet detection
* Better multi-object tracking
* Optical-flow-based motion estimation
* Non-linear trajectory prediction
* Attack-pattern recognition
* Learned collision prediction
* Reinforcement learning
* A learned movement policy

All of these were outside the scope of the original experiment.

---

## 📚 What I Learned

The most interesting part of this experiment was realizing that a seemingly simple task like **"avoid bullets"** quickly turns into a combination of several engineering problems.

The agent has to answer:

```
Where am I?
Where are the bullets?
Where are they going?
Where can I move?
Which position is safest?
How quickly should I react?
```

Even without machine learning, these questions naturally lead into:

* Perception
* State estimation
* Prediction
* Planning
* Control

So the project wasn't really about making a perfect Touhou bot.

It was about exploring the basic architecture of a real-time game agent and seeing how far a relatively simple approach could go.

---

## 📌 Final Note

This is a small experiment, not a finished product.

It was built to answer a question, not to become a long-term project.

The answer was interesting enough to keep the code around.

> **See the screen. Predict the danger. Find somewhere safer.**

That's it.
