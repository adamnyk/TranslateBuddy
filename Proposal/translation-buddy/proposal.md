# Translation Buddy

## What goal will your website be designed to achieve?

Translation buddy will enable users to translate words or phrases from and to the language of their choice. Under their profie, users can save favorite words and create collections of words to be refered to later or shared with all users.

## What kind of users will visit your site? In other words, what is the demographic of your users?

The users of this site are people who are learning a new language or are visitng another contry and want to remember frequently used phrases and be able refer to them quickly for study. 

## What data do you plan on using?

I plan to use translation data from Google's Translation API. A python client library is available. 

## In brief, outline your approach to creating your project 

Answer questions like the ones below, but feel free to add more information:

### What does your database schema look like?

### ![translation-buddy-diagram](/Proposal/translation-buddy/translation-buddy-diagram.png)

### What kinds of issues might you run into with your api?

- 3 month trial for Google Cloud services
- 500,000 characters/month free limit

### Is there any sensitive information you need to secure?

The user's password

### What functionality will your app include?

**Core Features**

- Translate words or phrases
- CRUD User
  - user / password authentication
- CRUD word lists

**Nice to have**

- Share word lists between users
- Input language detection
- Audio pronuncation
- Provide recommended starter phrases
- User written translation notes 
  - (pronunciation, mnemonics, formality, regional differences, etc.)
- Transliteration into user's native alphabet

### What will the user flow look like?

1. Register user / sign in
   1. Yes - continue
   2. No - site retains only basic translation featues

2. Se
3. Add translation to favorites or a list
4. Share list with other users

###  What features make your site more than CRUD? Do you have any stretch goals?

