# Evolve

Evolutionary Vigilant Optimizing Verifying Executor (EVOLVE): Process watcher for scripted languages that not only detects crashes and restarts the application, but also heals the code so it doesn't happen again.


# What is it?

Evolve is a powerful and flexible project by aiXcelus, designed to cater to a wide range of applications. This repository provides two implementations of Evolve - a Python version and a Node.js version. Users only need to choose one of the implementations based on their system requirements or preferences. The Node.js version is provided for full-stack systems where a current version of Python might not be available.

## Python Version

### Prerequisites

- Python 3.6 or higher

### Installation

1. Clone the repository:
```bash
   git clone https://github.com/aixcelus/evolve.git
   cd evolve
 ```
2. Set up a virtual environment (optional, but recommended):    
```
    python3 -m venv venv
    source venv/bin/activate
```
3. Install the required Python packages:
```
    pip install -r requirements.txt
```
4. Run the application:
```
    python3 evolve.py <runtime> <script>
```
    or
```
evolve <runtime> <script>
```

## Node.js Version

### Prerequisites

Node.js 12.0 or higher

### Installation

1. Clone the repository:
Same as in python version

2. Install the required Node.js packages:
```
    npm install
```
3. Run the application:
```
    evolve.js <runtime> <script>
```

## Support and Contributions

If you have any questions or need assistance, feel free to reach out to the aiXcelus team. We welcome contributions to improve and extend Evolve. To contribute, please submit a pull request with your changes.

Thank you for using Evolve from aiXcelus, and happy evolving!