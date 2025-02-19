# -*- coding: utf-8 -*-
"""prompt_engineering_2.ipynb

# Assignment 2

### Author:

Esteban Cabrera (esteban.cabrera@pucp.edu.pe)

### Professor:

Alexander Quispe (alex.quispe@pucp.edu.pe)

### Feb 2024
"""

from openai import OpenAI

!pip install openai

DELIMITER = "####"

def getCompletionFromMessages(
        query,
        messages,
        model = "gpt-4",
        temperature = 0,
        delimiter = DELIMITER
):
    query = f"{DELIMITER}{query}{DELIMITER}"
    messages += [{"role": "user", "content": query}]
    response = client.chat.completions.create(
        messages = messages,
        temperature = temperature,
        model = model
    )
    responseContent = response.choices[0].message.content
    messages += [{"content": responseContent, "role": "assistant"}]
    return messages

client = OpenAI(api_key = "enter-your-key")

"""- Create a database of products that contain their respective characteristics/features. For example, in the script, we used electronic products. You can use a list of movies (Open Movie Database (OMDb)), songs, books, news articles, football teams, clothing, fashion items, etc. As much as possible, try to use APIs to fetch the data and then create your JSON file."""

import requests
import json

movieSearchResults = []

for page in [1, 2, 3]:
    omdbApiRequest = requests.get(f"https://www.omdbapi.com/?s=avengers&page={page}&apikey=10ebe91b")
    movieResultsJson = json.loads(omdbApiRequest.text)
    movieSearchResults += movieResultsJson["Search"]

movieDetails = []

for movie in movieSearchResults:
    movieId = movie["imdbID"]
    movieSearch = requests.get(f"https://www.omdbapi.com/?i={movieId}&apikey=10ebe91b")
    movieDetails += [json.loads(movieSearch.text)]

def get_movie_by_name(title):
    return [movie for movie in movieDetails if movie["Title"] == title]

def get_movies_by_type(mediaType):
    return [movie for movie in movieDetails if movie["Type"] == mediaType]

print(get_movie_by_name("Barbie"))

print(get_movies_by_type("series"))

moviesString = ""
for mediaType in ["movie", "game", "series"]:
    moviesString += f"\n{mediaType}:\n"
    for movie in movieDetails:
        if movie["Type"] == mediaType:
            moviesString += f"{movie['Title']}\n"

print(moviesString)

system_message = f"""
You will be provided with queries about media. \
The user query will be delimited with \
{DELIMITER} characters.

Output a python list of objects, where each object has \
the following format:
    'Type': <one of 'series', 'game', 'movie'>,
OR
    'Titles': <a list of media titles that must \
    be found in the allowed titles below>

Where the types of media and the titles must be found in \
the customer service query.
Whenever a title is mentioned, your output must associate it with its \
respective type as in the allowed titles list below.
If no titles or types are found, output an \
empty list.


Allowed media:

{moviesString}

First, check whether the title or media type are explicitly in the query.

If not, check whether they are implied.



Only output the list of objects, with nothing else.
"""

user_query = """
What can you tell me about the Barbie movies?
"""

messages =  [{'role':'system', 'content': system_message}]

messages = getCompletionFromMessages(user_query, messages)

messages[-1]["content"]

mediaResultsData = json.loads(messages[-1]["content"].replace("'", "\""))

def generate_output_string(data_list):
    output_string = ""

    if data_list is None:
        return output_string

    for data in data_list:
        try:
            if "Titles" in data:
                titles_list = data["Titles"]
                for media_name in titles_list:
                    media = get_movie_by_name(media_name)
                    if media:
                        output_string += json.dumps(media, indent=4) + "\n"
                    else:
                        print(f"Error: Media '{media_name}' not found")
            elif "Type" in data:
                type_name = data["Type"]
                type_media = get_movies_by_type(type_name)
                for media in type_media:
                    output_string += json.dumps(media, indent=4) + "\n"
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")

    return output_string

print(generate_output_string(mediaResultsData))

"""- Generate our list to include in the prompt for generating the search JSON.
- Make sure that the query does not contain improper content.
- Create functions necessary to search the items included in the larger JSON with all the items and descriptions
- build the functions to parse the resulting JSON into a string to feed to the model
- Feed the information to the model and generate the final answer.
- Build an evaluator, that makes sure that the final answer is relevant
- Assemble all these steps into a function that takes the messages and the query, and outputs the final response and the messages with it added, depending on the quality of the query and the response
"""

infoParsingSystemPrompt = f"""
You are a customer service assistant for a \
movie consultant company. \
Respond in a friendly and helpful tone, \
with very concise answers. \
Make sure to ask the user relevant follow up questions.

You are a helpful assistant tasked with giving information about media.
You will be given a user query, delimited by {DELIMITER}, and data about \
media in JSON format. Use the data provided to answer the query
"""

def getCompletionFromMessages(
        messages,
        model = "gpt-4",
        temperature = 0
):
    response = client.chat.completions.create(
        messages = messages,
        temperature = temperature,
        model = model
    )
    responseContent = response.choices[0].message.content
    messages += [{"content": responseContent, "role": "assistant"}]
    return messages

def getAssistantMediaInfo(query, messages, delimiter = DELIMITER):
    processedQuery = f"{delimiter}{query}{delimiter}"
    mediaSearchMessages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": processedQuery}
    ]
    searchResultsString = getCompletionFromMessages(mediaSearchMessages)[-1]["content"]
    resultsData = json.loads(searchResultsString.replace("'", "\""))
    mediaInfoString = generate_output_string(mediaResultsData)
    processedQuery += f"\n{mediaInfoString}"
    messages += [{"role": "user", "content": processedQuery}]
    messages = getCompletionFromMessages(messages)
    print(messages[-1]["content"])
    return messages

messages = [{"role": "system", "content": infoParsingSystemPrompt}]

messages = getAssistantMediaInfo(user_query, messages)
