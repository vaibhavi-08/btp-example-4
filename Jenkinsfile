// pipeline {
//     agent any

//     options {
//         timestamps()
//     }

//     stages {

//         stage('Checkout') {
//             steps {
//                 checkout scm
//             }
//         }

//         stage('Setup') {
//             steps {
//                 sh '''
//                     set -e
//                     python3 -m venv venv
//                     . venv/bin/activate
//                     pip install --upgrade pip

//                     if [ -f requirements.txt ]; then
//                         pip install -r requirements.txt
//                     else
//                         echo "requirements.txt not found, skipping dependency install"
//                     fi
//                 '''
//             }
//         }

//         stage('Quality') {
//             steps {
//                 sh '''
//                     set -e
//                     . venv/bin/activate

//                     # Run black only on your project (optional: adjust paths)
//                     black --check .

//                     # Run flake8 but ignore venv and common junk dirs
//                     flake8 . --exclude=venv,.venv,.git,__pycache__
//                 '''
//             }
//         }


//         stage('Build') {
//             steps {
//                 sh '''
//                     set -e
//                     docker build -t my-app-image:latest .
//                 '''
//             }
//         }

//         stage('Tests') {
//             steps {
//                 sh '''
//                     set -e
//                     . venv/bin/activate
//                     pytest
//                 '''
//             }
//         }

//         stage('Deploy') {
//             steps {
//                 sh '''
//                     set -e

//                     CONTAINER_NAME="my-app-container"

//                     # Stop existing container if running
//                     if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
//                         echo "Stopping existing container..."
//                         docker stop $CONTAINER_NAME
//                     fi

//                     # Remove old container if exists (running or stopped)
//                     if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
//                         echo "Removing old container..."
//                         docker rm $CONTAINER_NAME
//                     fi

//                     # Run new container (modify port mapping if needed)
//                     echo "Starting new container from latest image..."
//                     docker run -d --name $CONTAINER_NAME -p 8000:8000 my-app-image:latest

//                     echo "Application deployed locally and running at: http://localhost:8000/"
//                 '''
//             }
//         }
//     }
// }
pipeline {
    agent any

    // We disable the default checkout so we can make it an explicit stage as you requested
    options { 
        skipDefaultCheckout() 
    }

    environment {
        IMAGE_NAME = "my-python-app"
        VENV_NAME = "venv"
    }

    stages {
        // 1. CHECKOUT: Get the code from Git
        stage('Checkout') {
            steps {
                echo 'Stage 1: Checkout SCM...'
                checkout scm
            }
        }

        // 2. SETUP: Create environment and install dependencies
        stage('Setup') {
            steps {
                echo 'Stage 2: Setup Virtual Environment...'
                // Create venv and install requirements
                sh """
                    python3 -m venv ${VENV_NAME}
                    . ${VENV_NAME}/bin/activate
                    pip install -r requirements.txt
                """
            }
        }

        // 3. QUALITY: Formatting and Linting (Black & Flake8)
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

        // 4. BUILD: Build the Docker Image
        stage('Build') {
            steps {
                echo 'Stage 4: Building Docker Image...'
                // Build the image tagged as 'latest'
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        // 5. TEST: Run Unit Tests (Pytest)
        stage('Test') {
            steps {
                echo 'Stage 5: Running Tests...'
                // We run tests INSIDE the Docker container to ensure the artifact works
                sh "docker run --rm ${IMAGE_NAME}:latest pytest"
            }
        }

        // 6. DEPLOY: Run the Container
        stage('Deploy') {
            steps {
                echo 'Stage 6: Deploying Application...'
                // Stop old container if running, then run new one
                sh """
                    docker stop ${IMAGE_NAME}_running || true
                    docker rm ${IMAGE_NAME}_running || true
                    docker run -d --name ${IMAGE_NAME}_running ${IMAGE_NAME}:latest
                """
            }
        }
    }

    post {
        always {
            echo 'Cleaning up workspace...'
            // Remove the virtual env and the docker image to save space
            sh "rm -rf ${VENV_NAME}"
            sh "docker rmi ${IMAGE_NAME}:latest || true"
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check logs.'
        }
    }
}