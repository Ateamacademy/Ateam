from datetime import date, timedelta
from flask import Flask, render_template, render_template_string
from EmailSender import * 
from Schema import *
import PyPDF2
import time
import re
import os
import random 
import string
import smtplib
import json
from flask import render_template_string
from jinja2 import Template
from weasyprint import HTML
import calendar
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from io import BytesIO
from pdf2image import convert_from_path

'''
 ____   ____     _    
|    | |    |  _| |_  
 |   |  |   | |_   _| 
 |   |  |   |   |_|   
 |   |  |   |         
 |   |  |   |         
 |___|  |___|         
 
 '''

#AB is to CD as BC is to DE
'''
usage:
generate_letters_pair(n) where n is the number of questions
take original letters and transformed code for the question and shift and direction for the answer
STILL NEED TO WRITE THE QUESTION
'''
def shift_letters():
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    shift_value = random.randint(1, 5)
    direction = random.choice(['left', 'right'])
    letter1, letter2 = random.sample(alphabet, 2)
    
    if direction == 'right':
        new_letter1 = alphabet[(alphabet.index(letter1) + shift_value) % 26]
        new_letter2 = alphabet[(alphabet.index(letter2) + shift_value) % 26]
    else:
        new_letter1 = alphabet[(alphabet.index(letter1) - shift_value) % 26]
        new_letter2 = alphabet[(alphabet.index(letter2) - shift_value) % 26]
    
    return {
        'Original Letters': letter1 + letter2,
        'Shift': shift_value,
        'Direction': direction,
        'Transformed Code': new_letter1 + new_letter2
    }
    
    
    
def generate_letter_pairs(n=5):
    return [shift_letters() for _ in range(n)]




# CODED WORDS
'''
Make sure to get long list of words and find the similar ones
Code works 
try with word_list = ["POUR", "RUDE", "TYPE", "DATE"]

usage: 
generate_word_codes(list) the list should be similar words (similar letters)


'''
def generate_word_codes(word_list):
    selected_words = random.sample(word_list, 4)  # Select 4 random words
    unique_letters = list(set("".join(selected_words)))  # Unique letters in selected words
    print(unique_letters)
    random.shuffle(unique_letters)
    letter_mapping = {}
    
    # Assign single-digit numbers to at most 6 unique letters
    for i, letter in enumerate(unique_letters):
        letter_mapping[letter] = str(i)
    
    # Create coded versions of the words
    coded_words = ["".join(letter_mapping.get(letter, "_") for letter in word) for word in selected_words]
    
    return list(zip(selected_words, coded_words))

def find_words_with_few_unique_letters(words):
    grouped_words = {}

    for word in words:
        unique_letters = frozenset(word)  # Using frozenset to make it hashable
        unique_count = len(unique_letters)

        if unique_count < 7:
            if unique_count not in grouped_words:
                grouped_words[unique_count] = []
            grouped_words[unique_count].append(word)

    for count, word_list in sorted(grouped_words.items()):
        print(f"Words with {count} unique letters: {word_list}")
        


# Letter Sequence
'''
usage: call letter_sequence_generator

lenght of terms is the length of reach entry
number of terms is the length of the list
harder = whther we include quadratcis or now

'''
def letter_sequence_generator(length_of_terms = 2, number_of_terms = 5, harder=False): 
    sequences = []
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    for _ in range(length_of_terms):
        a = random.randint(1, 5) if harder else 0  # Quadratic term
        b = random.randint(-9, 9)  # Linear term
        c = random.randint(0, 25)  # Constant term
        
        sequence = [(a * (n ** 2) + b * n + c) % 26 for n in range(1, number_of_terms + 1)]
        sequences.append("".join(alphabet[i] for i in sequence))
    
    overall_sequence = " ".join("".join(seq[i] for seq in sequences) for i in range(number_of_terms))
    return overall_sequence




#Synonyms, Antonyms
def synonym_generator(words_in_group):
    with open('/var/www/webApp/webApp/static/syn_ant_sent_sim.json', 'r') as file:
        data = json.load(file)

    # Pick a random word from the dataset
    random_entry = random.choice(data)
    word = random_entry["word"]

    # Get a list of synonyms
    synonyms = [syn["synonym"] for syn in random_entry["syn_list"]]

    # Ensure there are synonyms available
    if not synonyms:
        print(f"No synonyms found for '{word}', try another word.")
    else:
        # Pick a random synonym
        synonym = random.choice(synonyms)

        # Select 4 additional words from the dataset that are not the chosen word or synonym
        other_words = random.sample(
            [entry["word"] for entry in data if entry["word"] not in {word, synonym}],
            4
        )

        # Form two groups of 3
        group1 = [word, other_words[0], other_words[1]]
        group2 = [synonym, other_words[2], other_words[3]]

        # Print results
        print(f"Original Word: {word}")
        print(f"Chosen Synonym: {synonym}")
        print("\nGroup 1:", group1)
        print("Group 2:", group2)