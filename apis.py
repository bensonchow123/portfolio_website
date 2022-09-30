import praw
import os

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

load_dotenv()
apis = Blueprint("apis",__name__)
reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                     client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                     username=os.environ['REDDIT_USERNAME'],
                     password=os.environ['REDDIT_PASSWORD'],
                     user_agent=os.environ['REDDIT_AGENT'])

@apis.route('/api/reddit', methods=['GET'])
def reddit_api():
    if "subreddit" in request.args:
        subreddit = reddit.subreddit("+".join([request.args['subreddit']]))
    else:
        return "Not a valid subreddit or have no subreddit in request"
    submission = get_submissions(subreddit)
    return jsonify(submission)

def get_submissions(subreddit):
    submissions = []
    for x in subreddit.top():
        if not x.stickied:
            if not x.is_self:
                submissions.append(x.url)
    return submissions