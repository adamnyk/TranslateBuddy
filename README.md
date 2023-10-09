# TranslateBuddy

TranslateBuddy allows you to easily translate phrases to and from a variety of languages. Save and make notes on your favorites for use during study or travel. Browse other user's phrasebooks to discover new phrases or share your own!

[Check out TranslateBuddy!](https://translate-buddy.herokuapp.com/](https://translate-buddy.onrender.com/)


## Features

### Language Translation

Users can translate words and phrases to and from a variety of supported languages whether they are logged out or are registered users. As language support of the DeepL API increases over time, new language options will automatically be available in TranslateBuddy. After receiving a translation, registered users can add a translation to one or more of their phrasebooks. 

### Phrasebooks

Registered users can save and organize their translations by adding them to 'phrasebooks'. Phrasebooks are associated with a pair of languages and can be shared with other users by togging their visibility. Private translation notes can be added by users to help them remember things like pronunciation, mnemonic devices, formality, or appropriate contexts.  Sorting and filtering by language, name, and date added is available to more easily locate phrasebooks of interest. 

### Public Phrasebooks

If logged in, users can view a page of all phrasebooks that other users have chosen to mark as 'public'. Using filtering / sorting, users can quickly find phrasebooks in their languages of interest. Translations in public phrasebooks can then be added to one or more of a user's personal phrasebooks. Alternatively, the whole public phrasebook can be copied to a user's profile for their later customization.

The intention of this feature was to add a social component to language learning and to reduce the time spend entering and saving common phrases. 


## User Flow

![User Flow](/proposal/images/user_flow.png)

## Database

Due to the ability to copy public translations and phrasebooks, the current database structure is designed to minimize the duplication of 'translation' data. Translation data is only deleted when it is determined that there are no longer any parent phrasebooks accessing them. Translation notes are stored on the join table, phrasebook_translation, and are therefore unique to each user. 

![translation-buddy-diagram](/proposal/translation-buddy-diagram.png)


## API

![DeepL Logo](/proposal/images/deepl-ar21.png)
[DeepL Translator API](https://www.deepl.com/pro-api?cta=header-pro-api)

TranslateBuddy processes translations through the DeepL translate API and uses it's Python client library. 

## Tech Stack

HTML, CSS, Javascript, Jinja, Python, Flask, PostgreSQL, SQLAlchemy 
