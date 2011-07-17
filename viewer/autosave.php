<?php
session_start();
include_once("functions.php");

$urlid = $_POST['urlid'];
$topic = $_POST['topic'];
$type = $_POST['type'];

if($type == "news")
{
    $sql = "update urllist set topic='".$topic."' where rowid='".$urlid."'"; 
}
elseif($type == "corpus")
{
    $sql = "update cat_corpus_cats_single set category='".$topic."' " .
        "where urlid='".$urlid."'";
}
mysql_query($sql);
?>
