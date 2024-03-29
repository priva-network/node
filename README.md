# Priva Node

Running a Priva Node allows you to provide compute to Priva Network and earn for it.

## Getting Started
These instructions will help you get the project up and running on your local machine for development and testing purposes.

### Prerequisites
Before you begin, ensure you have the following installed on your system:

- Python 3.8 or newer
- pip (Python package installer)

### Install
Follow these steps to set up your development environment:

1. Clone the repository:
```bash
git clone https://github.com/priva-network/node.git
```
2. Navigate to the repository directory:
```bash
cd yourrepository
```
3. Install the required packages:
```bash
pip install -r requirements.txt
```
4. Install a compatible version of PyTorch:
Depending on your system (whether you have CUDA installed or not), you may need to install a specific version of PyTorch. Visit the PyTorch installation guide to find the command that matches your environment.

### Setup
To setup the node, run the following command:
```bash
python main.py setup
```
And follow the instructions outtputed to the console.

## Running the Node
To run the node, run the following command:

```bash
python main.py run
```
### Running in the Background
It's recommended to run the application in the background.

You can do this using nohup. Make sure you have to specify your wallet address in an environment variable:
```bash
WALLET_PASSWORD=YOUR_PASSWORD nohup python main.py run &
```
Logs and any output will be directed to nohup.out.

### Stopping the Application
To stop the background application, follow these steps:

1. Find the process ID (PID):
```bash
ps ax | grep main.py
```
1. Terminate the process using its PID:
```bash
kill -9 PID
```
Replace PID with the actual process ID you find.
