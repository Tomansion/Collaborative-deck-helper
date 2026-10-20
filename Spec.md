# Collaborative Deck Helper specification

This web app is designed to assist users in creating and managing collaborative decks of cards. At the moment, this app is tailored for the 5kings card game, but it can be adapted for other card games in the future.

- The app lists the available cards for each color
  - There are 5 colors: 
    - Coeur: Red
    - Carreau: Blue
    - Trèfle: Green
    - Pique: Violet
    - Star: Yellow
  - Cards go, for each color, from 3 to 10, then V, D and R.
  - There are 6 jokers
- Users can upload an image from their computer to represent a card.
  - If an image is added onto a previous image, it will be replaced, be we can still see the previous image in the history.
  - We can change the current image to a previous one in the history.
  - Users can see all the cards and their chosen images.
- There is a single deck that is shared between all users.
- Cards have their title (the value of the card) and a free text description that can be edited.
  - Default on first boot description are given in the default_descriptions.md file, this file serves for the spec
- Editing a description or an image on one computer will update the description or image on all other computers that are connected to the deck.
- Each cards has an overlay representing the color of the card, you are tasked of making an algorithm that will generate the overlay color based on the color and value of the card, and for the jester.
  - Images in the root of this folder represent the cards we want to mimic
- Each change is logged in a history, and users can see the history of changes made to the deck with date.
- We can download off the cards in a zip file, with the chosen image + overlay merged together
- The app is in French, a description, on top of the app describes the app and how to use it. The goal is to make a custom set of cards for a gift
- Technically:
  - Vuejs Option API
  - FastAPI backend
  - SQLite database
  - Images are saved in a folder on the server, and their paths are stored in the database.
  - Single docker build
  - Readme describing how to run the app in development and production mode
  - Commit after each step of the development