# Translation Buddy

## Website Goal

Translation buddy will enable users to translate words or phrases from and to the language of their choice. Under their profile, users can save favorite words and create collections of words to be referred to later or shared with all users.

## User Demographics

The users of this site are people who are learning a new language or are visiting another country and want to look up and reference frequently used phrases.

## Data Usage

I plan to use translation data from [DeepL Translator](https://www.deepl.com/translator). A python client library is also available.

## Approach

### Database Schema

### ![translation-buddy-diagram](/proposal/translation-buddy-diagram.png)

### Potential API issues

- 500,000 characters/month free limit
- No transliteration into Latin script (limited useful language support)

### Sensitive information to secure

User login passwords

### App Functionality

**Core Features**

- Translate words or phrases
- CRUD User
  - user / password authentication
- CRUD word lists
- User written translation notes
  - (pronunciation, mnemonics, formality, regional differences, etc.)

**Nice to have features**

- Create downloadable / printable study list (from list or imported file of phrases)
- Share word lists between users
- Provide recommended starter phrases

**Potential future features**

- Audio pronunciation (text to speech)
- Transliteration into user's native alphabet

### User Flow

1. Register user / sign in
   1. Yes - continue
   2. No - site retains only basic translation features
2. Logged in users can translate phrases and add custom notes
3. Users can create lists (phrasebooks) to save and organize their favorite translations or share them with other users
4. Users can export their phrasebooks to a printable / downloadable form for easy reference when traveling
   1. To create 'cheat sheets' more efficiently, users can upload a list of phrases in a .txt document and receive a new file with side by side translations.

### Beyond CRUD / stretch goals

- Create downloadable / printable 'cheat sheet' from an uploaded user document or user phrasebooks
