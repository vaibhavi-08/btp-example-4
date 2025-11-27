pipeline {
    agent any

    options {
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    set -e
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip

                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    else
                        echo "requirements.txt not found, skipping dependency install"
                    fi
                '''
            }
        }

        stage('Quality') {
            steps {
                sh '''
                    set -e
                    . venv/bin/activate

                    # Run black only on your project (optional: adjust paths)
                    black --check .

                    # Run flake8 but ignore venv and common junk dirs
                    flake8 . --exclude=venv,.venv,.git,__pycache__
                '''
            }
        }


        stage('Build') {
            steps {
                sh '''
                    set -e
                    docker build -t my-app-image:latest .
                '''
            }
        }

        stage('Tests') {
            steps {
                sh '''
                    set -e
                    . venv/bin/activate
                    pytest
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -e

                    CONTAINER_NAME="my-app-container"

                    # Stop existing container if running
                    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
                        echo "Stopping existing container..."
                        docker stop $CONTAINER_NAME
                    fi

                    # Remove old container if exists (running or stopped)
                    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
                        echo "Removing old container..."
                        docker rm $CONTAINER_NAME
                    fi

                    # Run new container (modify port mapping if needed)
                    echo "Starting new container from latest image..."
                    docker run -d --name $CONTAINER_NAME -p 8000:8000 my-app-image:latest

                    echo "Application deployed locally and running at: http://localhost:8000/"
                '''
            }
        }
    }
}
