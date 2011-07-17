<?php
$type = "news";
if(array_key_exists('type', $_GET) && $_GET['type'] == "corpus")
{ $type = "corpus"; }
?>
<?php include_once("header.php");?>
<?php include_once("functions.php");?>
<script src='rating/jquery.MetaData.js' type="text/javascript" language="javascript"></script>
<script src='rating/jquery.rating.js' type="text/javascript" language="javascript"></script>
<link href='rating/jquery.rating.css' type="text/css" rel="stylesheet"/>

<script type="text/javascript">
function save(urlid, topic) 
{ 
    /*alert("Update "+ urlid + " to "+ topic);*/
    $.post("autosave.php",
        {
            type: "<?php echo $type ?>",
            urlid: urlid,
            topic: topic
         },
         function(message) 
         { }
    );
};

$(function(){
 $('.auto-submit-star').rating({
  callback: function(value, link){
   // 'this' is the hidden form element holding the current value
   // 'value' is the value selected
   // 'element' points to the link element that received the click.
   
   $.post("autorate.php",
        {
           urlid: this.form.id.substring(8),
           rate: value,
           type: "<?php echo $type ?>",
         },
         function(message) 
         { }
    );
   
   // To submit the form automatically:
   //this.form.submit();
   
   // To submit the form via ajax:
   $(this.form).ajaxSubmit();
   
  }
 });
});

</script>

<?php $topics = array("AIOverview", "Agents", "Applications", 
"CognitiveScience", "Education", "Ethics", "Games", "History", "Interfaces", 
"MachineLearning", "NaturalLanguage", "Philosophy", "Reasoning", 
"Representation", "Robots", "ScienceFiction", "Speech", "Systems", "Vision", 
"NotRelated"); ?>

    <div id="page">
    <div id="page-bgtop">
    <div id="page-bgbtm">
        <div id="content">
            
            <?php
                if(isset($_REQUEST['page']))
                    { $page=$_REQUEST['page']; }
                else 
                    { $page = 1; }
                $pagerecords = 10;
                $start_from = ($page-1)*$pagerecords;

                if($type == "news")
                {
                    $query = "SELECT rowid as urlid,url,rate,adminrate,topic," .
                        "title,description,publisher,pubdate from urllist " .
                        "ORDER BY rowid DESC LIMIT $start_from, $pagerecords"; 
                }
                else if($type == "corpus")
                {
                    $query = "SELECT c.urlid,c.url,c.title,c.adminrate," .
                        "c.content,cc.category as topic " .
                        "FROM cat_corpus as c, cat_corpus_cats_single as cc " .
                        "WHERE c.urlid = cc.urlid " .
                        "ORDER BY c.urlid DESC LIMIT $start_from, $pagerecords";
                }
                $result = mysql_query( $query );
                if (!$result)
                {
                    die("Could not query the url table in the database: <br />" .
                        mysql_error());
                }
                while($result_row = mysql_fetch_array($result)){ 
            ?>
            <div class="post">
            <div class="post-bgtop">
            <div class="post-bgbtm">

                <h1 class="title">
                    <a target="_blank" href="<?php
                        echo stripslashes($result_row['url']);
                    ?>"><?php echo $result_row['title'];?></a></h1>

                <form style="padding-left:1.5em;" id=<?php
                    echo "starrate".$result_row['urlid'];
                ?> name=<?php echo getenv("REMOTE_ADDR")?> action="autorate.php">

                <?php for($i = 0; $i <= 5; $i++): ?>
                <input name=<?php echo "star".$result_row['urlid'];?>
                    value="<?php echo $i ?>" type="radio" class="auto-submit-star"
                    <?php
                        $rate = 'NULL';
                        if(array_key_exists('rate', $result_row))
                        {
                            $rate = $result_row['rate'];
                        }
                        if($result_row['adminrate'] != 'NULL')
                        {
                            $rate = $result_row['adminrate'];
                        }
                        if($rate <= $i && $rate > ($i-1)) echo " checked"; ?> />
                <?php endfor; ?>

                <input type="hidden" value=<?php
                    echo $result_row['urlid'];?> name="starurlid" />
                <input type="hidden" value=<?php
                    echo getenv("REMOTE_ADDR")?> name="ipaddress" />
                <input type="hidden" value=<?php echo $type ?> name="type" />
                
                </form>
                <p class="meta">&nbsp;&bull;&nbsp;
                    <?php if($type == "news"): ?>
                    Posted by <a target="_blank" href="<?php
                        echo stripslashes($result_row['url']);
                    ?>"><?php echo $result_row['publisher'];?></a>
                    on <?php echo $result_row['pubdate'];?>
                    &nbsp;&bull;&nbsp;</a>
                    <?php endif; ?>
                    <?php $selectid = $result_row['urlid']; ?>
                    
                    <select name=<?php echo $selectid;?> id=<?php echo $selectid;?>
                    onchange="save(this.id, this.options[this.selectedIndex].value);">
                    <?php 
                        $curr_topic = stripslashes($result_row['topic']);
                        foreach($topics as $topic){
                            $str =  "<option value = \"".$topic."\"";   
                            if($topic == $curr_topic){ $str .= " selected";}
                            $str.=">".$topic."</option>";
                            echo $str;
                        }
                    ?>   
                    </select>
                    &nbsp;&bull;&nbsp;
                    <span style="font-style:italic; font-size:0.8em;">
                    &nbsp;&nbsp;&nbsp;
                    <a target="_blank" href="<?php
                         echo stripslashes($result_row['url']);
                    ?>" class="permalink">Full article</a></span>

                    &nbsp;&bull;&nbsp;ID:<?php echo $result_row['urlid'];?>
                </p>
               
                <?php if($type == "news"): ?>
                <div class="entry"> <?php echo $result_row['description'];?></div>
                <?php elseif($type == "corpus"): ?>
                <div class="entry" style="height: 200px; overflow: auto">
                <?php echo preg_replace("/\n/", '<br/>', $result_row['content']); ?>
                </div>
                <?php endif; ?>
            </div>
            </div>
            </div>
             <?php }?>

            <!-- Start of Pagination-->
            <div style="margin-top:20px">
              <ul id="pagination-digg" style="text-align:center;">
               <?php if($page!=1) {?>
                <li class="previous"> 
                <a href="?type=<?php echo $type ?>&page=<?php if($page!=1) echo $page-1; else echo '1';?>">&laquo;Previous</a>
                </li>
                <?php }?>
                             
                <?php
                if($type == "news")
                {
                    $countquery = "SELECT COUNT(*) FROM urllist";
                }
                else if($type == "corpus")
                {
                    $countquery = "SELECT COUNT(*) FROM cat_corpus";
                }
                $countresult = mysql_query( $countquery );                                      
                if (!$countresult)  {
                       die ("countRecords in the search.php failed. Could not query the database: <br />". mysql_error());
                }
                $result_count_row=mysql_fetch_row($countresult);
                $records=$result_count_row[0];
                
                $total_pages=ceil($records/$pagerecords);
                {
                    for ($i=1; $i<=$total_pages; $i++) {
                        echo "<li><a href='?type=$type&page=".$i."'";
                        if($i==$page)
                            echo " class='active' ";
                        echo ">".$i."</a></li> ";
                    };
                }
                ?>       
                    
                <?php if($page!=$total_pages) {?>       
                <li class="next">
                <a href="?type=<?php echo $type ?>&page=<?php if($page!=$total_pages) echo $page+1; else echo $total_pages;?>">
                Next &raquo;</a>
                </li>
                <?php }?>
                </ul>
            </div>
            <!-- End of Pagination-->
        <div style="clear: both;">&nbsp;</div>
        </div>
        <!-- end #content -->
    <?php include_once('sidebar.php');?>
    <?php include_once('footer.php');?>
