# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./web_app/* /app/

# Install any needed packages specified in requirements.txt
RUN apt-get update -yy && apt-get install zip unzip -yy

CMD pip install --target . -r requirements.txt && zip -r web_app_lambda.zip ./* && rm -r psycopg2*