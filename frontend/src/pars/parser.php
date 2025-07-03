<?php

require_once __DIR__ . '/vendor/autoload.php';
require_once __DIR__ . '/vendor/simplehtmldom/simplehtmldom/simple_html_dom.php';

use RedBeanPHP\R as R;

R::setup('sqlite:db_zabir_2.db');

$sitemap = new DOMDocument;
$sitemap->load("sitemap_zab_9_12.xml");
$urls = $sitemap->getElementsByTagName("url");

$startIndex = 3357; // Индекс начинается с 0, поэтому 3358-й URL будет иметь индекс 3357
$currentIndex = 0;
$article_counter = 1; // Инициализация счетчика статей
$batchSize = 500; // Размер блока

foreach ($urls as $key => $url) {
    if ($currentIndex < $startIndex) {
        $currentIndex++;
        continue;
    }

    $locs = $url->getElementsByTagName("loc");
    $loc = $locs->item(0)->nodeValue;
    $resp = file_get_contents($loc);
    
    // Проверка успешной загрузки страницы
    if ($resp === false) {
        echo "Failed to fetch URL: $loc\n";
        $currentIndex++;
        continue;
    }

    $html = str_get_html($resp);

    // Проверка наличия элемента main.content
    $content = $html->find("main.content", 0);
    if (!$content) {
        echo "Content not found in URL: $loc\n";
        $currentIndex++;
        continue;
    }

    // Проверка наличия h1 внутри main.content
    $article_name_element = $html->find("main.content h1", 0);
    if (!$article_name_element) {
        echo "Article name not found in URL: $loc\n";
        $currentIndex++;
        continue;
    }
    $article_name = $article_name_element->innertext;

    // Проверка наличия мета-тега description
    $meta_description = $html->find("meta[name=description]", 0);
    $meta_description_content = $meta_description ? $meta_description->content : '';

    $new_bean = R::dispense("articles");
    $new_bean->content = $content->innertext;
    $new_bean->name = $article_name;
    $new_bean->url = TranslitURL($article_name);
    $new_bean->metaTags = $meta_description_content;
    R::store($new_bean);

    // Вывод сообщения в консоль после сохранения статьи
    echo "Статья номер $article_counter загружена для забира. Тема: $article_name\n";
    $article_counter++; // Увеличение счетчика статей

    $currentIndex++;

    // Проверка на размер блока и пауза
    if ($currentIndex % $batchSize === 0) {
        echo "Обработано $currentIndex статей. Ожидание перед следующим блоком...\n";
        sleep(10); // Пауза в 10 секунд перед следующим блоком
    }
}

function TranslitURL($text)
{
    $RU['ru'] = array(
        'Ё', 'Ж', 'Ц', 'Ч', 'Щ', 'Ш', 'Ы',
        'Э', 'Ю', 'Я', 'ё', 'ж', 'ц', 'ч',
        'ш', 'щ', 'ы', 'э', 'ю', 'я', 'А',
        'Б', 'В', 'Г', 'Д', 'Е', 'З', 'И',
        'Й', 'К', 'Л', 'М', 'Н', 'О', 'П',
        'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ъ',
        'Ь', 'а', 'б', 'в', 'г', 'д', 'е',
        'з', 'и', 'й', 'к', 'л', 'м', 'н',
        'о', 'п', 'р', 'с', 'т', 'у', 'ф',
        'х', 'ъ', 'ь', '/'
    );

    $EN['en'] = array(
        "Yo", "Zh",  "Cz", "Ch", "Shh", "Sh", "Y'",
        "E'", "Yu",  "Ya", "yo", "zh", "cz", "ch",
        "sh", "shh", "y'", "e'", "yu", "ya", "A",
        "B", "V",  "G",  "D",  "E",  "Z",  "I",
        "J",  "K",   "L",  "M",  "N",  "O",  "P",
        "R",  "S",   "T",  "U",  "F",  "Kh",  "''",
        "'",  "a",   "b",  "v",  "g",  "d",  "e",
        "z",  "i",   "j",  "k",  "l",  "m",  "n",
        "o",  "p",   "r",  "s",  "t",  "u",  "f",
        "h",  "''",  "'",  "-"
    );
    $t = str_replace($RU['ru'], $EN['en'], $text);
    $t = preg_replace("/[\s]+/u", "_", $t);
    $t = preg_replace("/[^a-z0-9_\-]/iu", "", $t);
    $t = strtolower($t);

    return $t;
}
?>