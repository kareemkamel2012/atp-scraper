FROM public.ecr.aws/lambda/python:3.12

# Install necessary tools
RUN microdnf install -y wget unzip tar gzip && \
    # Download Google Chrome
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm && \
    # Install Google Chrome
    microdnf install -y google-chrome-stable_current_x86_64.rpm && \
    # Clean up the downloaded RPM
    rm google-chrome-stable_current_x86_64.rpm && \
    # Get the latest ChromeDriver version
    CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    # Download ChromeDriver
    wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    # Unzip ChromeDriver and clean up
    unzip chromedriver_linux64.zip -d /usr/bin && \
    rm chromedriver_linux64.zip && \
    microdnf clean all

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY scraper.py entrypoint.py ${LAMBDA_TASK_ROOT}

CMD ["entrypoint.lambda_handler"]
