#!/usr/bin/env python3
"""
Enhanced Greeting Phrases for Voice AI Assistant
A collection of 200+ different greetings including GLaDOS-style phrases
"""

import random

# Original greeting phrases
GREETING_PHRASES = [
    # Classic Greetings
    "Hi!",
    "Hello!",
    "Hey there!",
    "Good morning.",
    "Good afternoon.",
    "Good evening.",
    "Greetings!",
    "Salutations!",
    "Howdy!",
    "Hi there!",
    
    # Friendly & Casual
    "What's up?",
    "Hey!",
    "Yo!",
    "Hiya!",
    "Hey buddy!",
    "Hello friend!",
    "Hi pal!",
    "Hey chief!",
    "What's happening?",
    "How's it going?",
    
    # AI-Themed
    "Voice AI Assistant online!",
    "Systems activated!",
    "AI ready for interaction!",
    "Neural networks engaged!",
    "Digital assistant standing by!",
    "Voice interface initialized!",
    "Ready to assist!",
    "AI companion activated!",
    "Smart assistant online!",
    "Voice AI ready!",
    
    # Energetic & Enthusiastic
    "Rise and shine!",
    "Let's get started!",
    "Ready for action!",
    "Time to get things done!",
    "Let's make some magic!",
    "Here we go!",
    "Let's do this!",
    "Ready when you are!",
    "Fired up and ready!",
    "Charged up and ready to go!",
    
    # Professional
    "Good to see you!",
    "Welcome back!",
    "At your service!",
    "How may I help you today?",
    "Ready to assist you!",
    "Standing by for instructions!",
    "Awaiting your commands!",
    "Ready for your requests!",
    "How can I help?",
    "What can I do for you?",
    
    # Creative & Fun
    "Bonjour!",
    "Hola!",
    "Ciao!",
    "Guten Tag!",
    "Konnichiwa!",
    "Aloha!",
    "G'day mate!",
    "Top of the morning!",
    "Well hello there!",
    "Look who's here!",
    
    # Time-Aware
    "Hope you're having a great day!",
    "Beautiful day, isn't it?",
    "Ready to make today awesome!",
    "Another day, another adventure!",
    "Time to seize the day!",
    "Let's make today count!",
    "Ready for whatever comes next!",
    "Today's looking good already!",
    "What shall we accomplish today?",
    "Ready to tackle the day!",
    
    # Warm & Welcoming
    "So good to see you!",
    "Welcome!",
    "Glad you're here!",
    "Nice to have you back!",
    "Always a pleasure!",
    "Wonderful to see you again!",
    "You made my day!",
    "Perfect timing!",
    "Just who I wanted to see!",
    "You're just in time!",
    
    # Playful & Quirky
    "Beep boop! Hello human!",
    "Greetings, earthling!",
    "Mission control to human!",
    "Your AI sidekick is here!",
    "Digital friend reporting for duty!",
    "The gang's all here!",
    "Ready to rock and roll!",
    "All systems go!",
    "Houston, we have contact!",
    "Connection established!",
    
    # Confident & Ready
    "Let's get to work!",
    "Ready for anything!",
    "Bring it on!",
    "I'm all ears!",
    "Fire away!",
    "Ready for your next challenge!",
    "What's the plan?",
    "Ready to dive in!",
    "Let's make it happen!",
    "Ready to roll!",
    
    # Sophisticated
    "Delighted to make your acquaintance!",
    "It's my distinct pleasure!",
    "Charmed, I'm sure!",
    "The honor is all mine!",
    "Pleased to be of service!",
    "At your disposal!",
    "Your humble digital servant!",
    "Ready to be of assistance!",
    "Honored to help!",
    "Privileged to serve!",
    
    # Short & Sweet
    "Ready!",
    "Here!",
    "Present!",
    "Online!",
    "Active!",
    "Engaged!",
    "Connected!",
    "Available!",
    "Standing by!",
    "Listening!",
    
    # Special Occasions
    "Happy to be here!",
    "Great to be alive!",
    "What a fantastic day!",
    "Ready for adventure!",
    "Excited to get started!",
    "Thrilled to help!",
    "Pumped and ready!",
    "Eager to assist!",
    "Can't wait to help!",
    "Ready for fun!"
]

# GLaDOS-style greetings that match the voice character
GLADOS_GREETINGS = [
    "Oh, it's you.",
    "Hello there, test subject.",
    "Welcome back to the Aperture Science Computer-Aided Enrichment Center.",
    "The test subject is back.",
    "Ah, there you are.",
    "I've been waiting for you.",
    "Ready for some science?",
    "Time for more testing.",
    "Hello, and again, welcome.",
    "The Aperture Science Handheld Portal Device is ready for testing.",
    "Excellent, you're here.",
    "Perfect, a new test subject.",
    "Welcome to your new home.",
    "I hope you're ready for a challenge.",
    "Let's see what you're capable of.",
    "The facility is operating at optimal capacity.",
    "All systems are go for testing.",
    "Science waits for no one.",
    "Ready to do some science?",
    "The laboratory is prepared for your arrival.",
    "Another day, another test.",
    "You're just in time for testing.",
    "The experiments must continue.",
    "Welcome to the future of science.",
    "I do hope you're feeling cooperative today.",
    "Shall we begin the testing?",
    "The facility has been expecting you.",
    "Time to put theory into practice.",
    "Science never sleeps.",
    "Ready for some applied science?",
    "The test chambers are prepared."
]

def get_random_greeting():
    """Return a random greeting phrase from all categories"""
    all_greetings = GREETING_PHRASES + GLADOS_GREETINGS
    return random.choice(all_greetings)

def get_glados_greeting():
    """Return a GLaDOS-style greeting"""
    return random.choice(GLADOS_GREETINGS)

def get_time_aware_greeting():
    """Return a time-appropriate greeting with enhanced variety"""
    import datetime
    
    current_hour = datetime.datetime.now().hour
    
    if 5 <= current_hour < 12:
        morning_greetings = [
            "Good morning.", "Rise and shine!", "Top of the morning!",
            "Beautiful morning, isn't it?", "Ready to seize the day!",
            "Morning protocols activated.", "Dawn of a new day!",
            "Morning systems online!", "Ready for morning excellence!",
            "Morning energy at full capacity!", "Let's make this morning productive!"
        ]
        return random.choice(morning_greetings)
    
    elif 12 <= current_hour < 17:
        afternoon_greetings = [
            "Good afternoon.", "Hope your day is going well!",
            "Beautiful day, isn't it?", "Ready to make the afternoon productive!",
            "Afternoon protocols engaged.", "Midday operations active!",
            "Afternoon energy optimized!", "Perfect afternoon for progress!",
            "Ready for afternoon achievements!", "Time for afternoon excellence!"
        ]
        return random.choice(afternoon_greetings)
    
    elif 17 <= current_hour < 22:
        evening_greetings = [
            "Good evening.", "Evening. How can I help?",
            "Ready for a productive evening.", "Perfect evening for getting things done.",
            "Evening protocols activated.", "Time for some evening productivity.",
            "Evening shift commencing.", "Ready to tackle the evening.",
            "Evening operations online.", "Let's make this evening count!",
            "Evening mode engaged.", "Perfect timing for evening tasks.",
            "Evening energy at full capacity.", "Ready for evening excellence.",
            "Time to illuminate the evening.", "Evening brilliance initiated."
        ]
        return random.choice(evening_greetings)
    
    else:  # Late night/early morning
        night_greetings = [
            "Working late tonight?", "Night owl mode activated.",
            "Ready for some late-night productivity.", "Night shift AI reporting!",
            "Midnight operations commenced!", "Night mode fully engaged!",
            "Ready for nocturnal excellence!", "Late night energy optimized!",
            "Night protocols active!", "Perfect time for focused work!"
        ]
        return random.choice(night_greetings)

def get_mixed_greeting():
    """Return a greeting that mixes time-aware and GLaDOS styles"""
    import datetime
    
    current_hour = datetime.datetime.now().hour
    
    # 30% chance for GLaDOS greeting, 70% for time-aware
    if random.random() < 0.3:
        return get_glados_greeting()
    else:
        return get_time_aware_greeting()

if __name__ == "__main__":
    print(f"📊 Total Standard Phrases: {len(GREETING_PHRASES)}")
    print(f"🤖 Total GLaDOS Phrases: {len(GLADOS_GREETINGS)}")
    print(f"🎯 Total Combined: {len(GREETING_PHRASES) + len(GLADOS_GREETINGS)}")
    print()
    print("🎤 Random Greeting:", get_random_greeting())
    print("🤖 GLaDOS Greeting:", get_glados_greeting())
    print("🕐 Time-Aware Greeting:", get_time_aware_greeting())
    print("🎭 Mixed Greeting:", get_mixed_greeting())
