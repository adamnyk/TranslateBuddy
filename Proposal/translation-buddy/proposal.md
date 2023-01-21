# Translation Buddy using [DeepL.com](https://www.deepl.com/translator)

## What goal will your website be designed to achieve?

Translation buddy will enable users to translate words or phrases from and to the language of their choice. Under their profie, users can save favorite words and create collections of words to be refered to later or shared with all users.

## What kind of users will visit your site? In other words, what is the demographic of your users?

The users of this site are people who are learning a new language or are visitng another contry and want to remember frequently used translations or refer to them quickly for study. 

## What data do you plan on using?

I plan to use translation data from [DeepL.com](https://www.deepl.com/translator) or a [LibreTranslate](https://libretranslate.com/) (may not be free).

> **I am unsure if this [translator python library](https://pypi.org/project/translate-api/#more-about-translators) would be useful. Ask mentor. **

## In brief, outline your approach to creating your project 

Answer questions like the ones below, but feel free to add more information:

### What does your database schema look like?

### ![translation-buddy-diagram](/Users/adampecan/Documents/Springboard/Exercises/34_Capstone_1/Proposal/translation-buddy/translation-buddy-diagram.png)

### What kinds of issues might you run into with your api?

- Requires Credit Card for colatteral agains abuse
- 500,000 characters/month free limit
- Tralnsliteration into roman alphabet or audio is not available
- May reqiure using client python library

### Is there any sensitive information you need to secure?

The user's password

### What functionality will your app include?

- CRUD User
- CRUD Favorites / word lists
- Share word lists

### What will the user flow look like?

1. Create an account or sign in (optional)
2. Input and recieve translation
3. Add translation to favorites or a list
4. Share list with other users

###  What features make your site more than CRUD? Do you have any stretch goals?

> **Ideas?** 
>
> - automatically link to an audio pronunciation search? [forvo.com](https://forvo.com/)?

## Questions

- DeepL offers a [client library](https://pypi.org/project/deepl/). Would using this defeat the point of the assignment?
- I don't think 