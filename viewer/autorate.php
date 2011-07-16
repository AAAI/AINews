<?php
session_start();
include_once("functions.php");

$urlid = $_REQUEST['urlid'];
$rate = $_REQUEST['rate'];
$type = $_REQUEST['type'];

if($type == "news")
{
    $sql = "update urllist set adminrate=".$rate." where rowid='".$urlid."'";
}
elseif($type == "corpus")
{
    $sql = "update cat_corpus set adminrate=".$rate." where urlid='".$urlid."'";
}
mysql_query($sql);
?>
