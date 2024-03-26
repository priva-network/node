# Priva Node

Running a Priva Node allows you to provide compute to Priva Network and earn for it.

## Getting Started
These instructions will help you get the project up and running on your local machine for development and testing purposes.

### Prerequisites
Before you begin, ensure you have the following installed on your system:

- Python 3.8 or newer
- pip (Python package installer)

### Installing
Follow these steps to set up your development environment:

1. Clone the repository:
```bash
git clone https://github.com/priva-network/node.git
```
1. Navigate to the repository directory:
```bash
cd yourrepository
```
1. Install the required packages:
```bash
pip install -r requirements.txt
```
1. Install a compatible version of PyTorch:
Depending on your system (whether you have CUDA installed or not), you may need to install a specific version of PyTorch. Visit the PyTorch installation guide to find the command that matches your environment.

## Running the Application
To start the application, run the following command:

```bash
PRIVA_ENV=production uvicorn application:app --host 0.0.0.0
```
### Running in the Background
It's recommended to run the application in the background.

1. Export the environment variable:
```bash
export PRIVA_ENV=production
```
1. Run the application in the background using nohup:
```bash
nohup uvicorn application:app --host 0.0.0.0 &
```
Logs and any output will be directed to nohup.out.

### Stopping the Application
To stop the background application, follow these steps:

1. Find the process ID (PID):
```bash
ps ax | grep uvicorn
```
1. Terminate the process using its PID:
```bash
kill -9 PID
```
Replace PID with the actual process ID you find.
