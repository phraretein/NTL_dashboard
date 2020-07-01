# NTL Dashboard
<p> This project serves as a process to pull data to visualize the performance of the chatbot with real users in production. All the codes in the <strong>/script</strong> folder that pulls raw data from database and transform it into an organized dataframe which can be further used for visualization. </p>

## Prerequisites
<p> All the library required are listed in <strong>requirements.txt</strong>.

## Result
<strong> fully implemented dashboard 👉🏻 </strong> https://datastudio.google.com/u/0/reporting/ab41afd6-7673-4c17-8bdb-eb8078ca96ef/page/VE1QB 👈🏻
### WordCloud
<p> This script will be executed on a monthly basis. The special feature about this script is it involves the use of <strong> NLP's TF-IDF technique</strong> in order to rank top 20 most frequent word input by the users. Moreover, those topwords are displayed as a wordcloud for aesthetics and easy-to-read purposes.
