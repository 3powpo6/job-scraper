import requests
from bs4 import BeautifulSoup
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime

slack_token = 'your-api-token-here'
slack_client = WebClient(token=slack_token)
slack_channel_jobs = '#jobs'
slack_channel_log = '#bot-log'

def scrape_website():
    url = "https://slo-tech.com/delo/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Get all job posts on the website
    jobs = soup.tbody
    # Count active job ads
    current_active_ads = len(jobs)
    # Get current latest job ID
    current_latest_job_id = jobs.a['href'].split("delo/",-1)[1]
    # Get latest job ID from previous run
    previous_latest_job_id = check_previous_id()

    results = []
    for job in jobs:
        job.id = job.a['href'].split("delo/", -1)[1]
        if job.id > previous_latest_job_id:
            position = job.a.text
            #tags = job.div.text
            company = job.contents[2].text
            date = datetime.strptime(job.time['datetime'], "%Y-%m-%dT%H:%M:%S%z")
            # Display date of the post into: DD.MM.YYYY @ HH:mm
            formatted_date = date.strftime("%d.%m.%Y @ %H:%M")
            results.append(f"{position} | {company} | posted on: {formatted_date} | {url}{job.id}")
    return results, current_active_ads, current_latest_job_id, previous_latest_job_id

def send_slack_message(slack_channel, text):
    try:
        slack_client.chat_postMessage(
            channel=slack_channel,
            text=text
        )
    except SlackApiError as e:
        log = f"Error posting message: {e}"
        save_log(log)
        print(log)

#Check latest job ID from previous run to avoid duplicates
def check_previous_id():
    try:
        f = open("latest", "r")
        return f.readline()
    except:
        log = "latest id not found, possibly first run"
        save_log(log)
        print(log)
        return "0"

#Save latest job ID to file 'latest', to avoid forwarding duplicates
def save_latest_id(id):
    f = open("latest", "w")
    f.write(id)
    f.close()
def main():
    results = scrape_website()
    new_jobs = len(results[0])
    total_jobs_found = results[1]
    latest_job_id = results[2]
    previous_latest_job_id = results[3]

    if new_jobs > 0:
        for result in reversed(results[0]):
            message = f"New job found: {result}"
            print(message)
            send_slack_message(slack_channel_jobs, message)
        latest_id = result.split("/delo/",2)[1]
        save_latest_id(latest_id)
        latest_job_id = latest_id

    report = f"Slo-Tech jobs actualized, {new_jobs} jobs added, {total_jobs_found} total found. Latest job ID: {latest_job_id}, previous latest job ID: {previous_latest_job_id}"
    save_log(f"{datetime.now()} - {report}")
    send_slack_message(slack_channel_log, report)
    print(report)


def save_log(event):
    log = open("log.txt", "a")
    log.write(event + "\n")
    log.close()

if __name__ == "__main__":
    main()