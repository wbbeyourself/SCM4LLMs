#!/bin/bash

book_zh_dir=data/book/ChineseBook
# book1=$book_zh_dir/哈利.波特中文版1.txt
# book2=$book_zh_dir/平凡的世界.txt
# book3=$book_zh_dir/三国演义.txt
book4=$book_zh_dir/三体.txt
# book5=$book_zh_dir/西游记.txt

book_en_dir=data/book/EnglishBook
# book6=$book_en_dir/The_Old_Man_and_the_Sea.txt
# book7=$book_en_dir/The_Great_Gatsby.txt
# book8=$book_en_dir/The_Life_and_Adventures_of_Robinson_Crusoe.txt
# book9=$book_en_dir/Jane_Eyre.txt
book10=$book_en_dir/Gone_With_The_Wind.txt

ENGINE_TURBO=gpt-3.5-turbo
ENGINE_DAVINCI_003=text-davinci-003


python book_summary.py --model_name $ENGINE_TURBO \
    --book_files $book4 $book10 \


python book_summary.py --model_name $ENGINE_DAVINCI_003 \
    --book_files $book4 $book10 \


python book_summary.py --model_name $ENGINE_TURBO \
    --book_files $book4 $book10 \
    --no_scm \


python book_summary.py --model_name $ENGINE_DAVINCI_003 \
    --book_files $book4 $book10 \
    --no_scm \


echo "run batch book summary done !!!"