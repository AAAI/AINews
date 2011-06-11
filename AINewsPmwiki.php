<?php
/*****************************************************************************
 *
 * AINewsPmwiki.php is used to read-in the AINewsRanker's output text,
 * then save the output text into PmWiki format.
 * The PageStore class is extracted from the pmwiki.php from PmWiki directory.
 *
 ******************************************************************************/
error_reporting(E_ALL ^ E_NOTICE);
$ini_array = parse_ini_file("config.ini", true);
$PMWIKI_DIR = $ini_array['pmwiki']['dir'];

chdir($PMWIKI_DIR);


/******************************************************************************
* 
*  Following code is extracted from pmwiki.php from the Pmwiki directory
*
******************************************************************************/
$FarmD = dirname(__FILE__);
$WorkDir = 'wiki.d';
$WikiDir = new PageStore('wiki.d/{$FullName}');
$WikiLibDirs = array(&$WikiDir,new PageStore('$FarmD/wikilib.d/{$FullName}'));
$Now=time();
define('READPAGE_CURRENT', $Now+604800);
$Version = 1.0;

class PageStore {
  var $dirfmt;
  var $iswrite;
  var $attr;
  function PageStore($d='$WorkDir/$FullName', $w=0, $a=NULL) { 
    $this->dirfmt = $d; $this->iswrite = $w; $this->attr = (array)$a;
    $GLOBALS['PageExistsCache'] = array();
  }
  function pagefile($pagename) {
    global $FarmD;
    $dfmt = $this->dirfmt;
    if ($pagename > '') {
      $pagename = str_replace('/', '.', $pagename);
      if ($dfmt == 'wiki.d/{$FullName}')               # optimizations for
        return "wiki.d/$pagename";                     # standard locations
      if ($dfmt == '$FarmD/wikilib.d/{$FullName}')     # 
        return "$FarmD/wikilib.d/$pagename";           #
      if ($dfmt == 'wiki.d/{$Group}/{$FullName}')
        return preg_replace('/([^.]+).*/', 'wiki.d/$1/$0', $pagename);
    }
    return FmtPageName($dfmt, $pagename);
  }
  function read($pagename, $since=0) {
    $newline = '';
    $urlencoded = false;
    $pagefile = $this->pagefile($pagename);
    if ($pagefile && ($fp=@fopen($pagefile, "r"))) {
      $page = $this->attr;
      while (!feof($fp)) {
        $line = fgets($fp, 4096);
        while (substr($line, -1, 1) != "\n" && !feof($fp)) 
          { $line .= fgets($fp, 4096); }
        $line = rtrim($line);
        if ($urlencoded) $line = urldecode(str_replace('+', '%2b', $line));
        @list($k,$v) = explode('=', $line, 2);
        if (!$k) continue;
        if ($k == 'version') { 
          $ordered = (strpos($v, 'ordered=1') !== false); 
          $urlencoded = (strpos($v, 'urlencoded=1') !== false); 
          if (strpos($v, 'pmwiki-0.')!==false) $newline="\262";
        }
        if ($k == 'newline') { $newline = $v; continue; }
        if ($since > 0 && preg_match('/:(\\d+)/', $k, $m) && $m[1] < $since) {
          if ($ordered) break;
          continue;
        }
        if ($newline) $v = str_replace($newline, "\n", $v);
        $page[$k] = $v;
      }
      fclose($fp);
    }
    return @$page;
  }
  function write($pagename,$page) {
    global $Now, $Version;
    $page['name'] = $pagename;
    $page['time'] = $Now;
    $page['host'] = $_SERVER['REMOTE_ADDR'];
    $page['agent'] = @$_SERVER['HTTP_USER_AGENT'];
    $page['rev'] = @$page['rev']+1;
    unset($page['version']); unset($page['newline']);
    uksort($page, 'CmpPageAttr');
    $s = false;
    $pagefile = $this->pagefile($pagename);
    $dir = dirname($pagefile); 
    //mkdirp($dir);
    if (!file_exists("$dir/.htaccess") && $fp = @fopen("$dir/.htaccess", "w")) 
      { fwrite($fp, "Order Deny,Allow\nDeny from all\n"); fclose($fp); }
    if ($pagefile && ($fp=fopen("$pagefile,new","w"))) {
      $r0 = array('%', "\n", '<');
      $r1 = array('%25', '%0a', '%3c');
      $x = "version=$Version ordered=1 urlencoded=1\n";
      $s = true && fputs($fp, $x); $sz = strlen($x);
      foreach($page as $k=>$v) 
        if ($k > '' && $k{0} != '=') {
          $x = str_replace($r0, $r1, "$k=$v") . "\n";
          $s = $s && fputs($fp, $x); $sz += strlen($x);
        }
      $s = fclose($fp) && $s;
      $s = $s && (filesize("$pagefile,new") > $sz * 0.95);
      if (file_exists($pagefile)) $s = $s && unlink($pagefile);
      $s = $s && rename("$pagefile,new", $pagefile);
    }
    $s && fixperms($pagefile);
    if (!$s)
      Abort("Cannot write page to $pagename ($pagefile)...changes not saved");
   
  }
  function exists($pagename) {
    if (!$pagename) return false;
    $pagefile = $this->pagefile($pagename);
    return ($pagefile && file_exists($pagefile));
  }
  function delete($pagename) {
    global $Now;
    $pagefile = $this->pagefile($pagename);
    @rename($pagefile,"$pagefile,del-$Now");
  }
  function ls($pats=NULL) {
    global $GroupPattern, $NamePattern;
    StopWatch("PageStore::ls begin {$this->dirfmt}");
    $pats=(array)$pats; 
    array_push($pats, "/^$GroupPattern\.$NamePattern$/");
    $dir = $this->pagefile('$Group.$Name');
    $maxslash = substr_count($dir, '/');
    $dirlist = array(preg_replace('!/*[^/]*\\$.*$!','',$dir));
    $out = array();
    while (count($dirlist)>0) {
      $dir = array_shift($dirlist);
      $dfp = @opendir($dir); if (!$dfp) { continue; }
      $dirslash = substr_count($dir, '/') + 1;
      $o = array();
      while ( ($pagefile = readdir($dfp)) !== false) {
        if ($pagefile{0} == '.') continue;
        if ($dirslash < $maxslash && is_dir("$dir/$pagefile"))
          { array_push($dirlist,"$dir/$pagefile"); continue; }
        if ($dirslash == $maxslash) $o[] = $pagefile;
      }
      closedir($dfp);
      StopWatch("PageStore::ls merge {$this->dirfmt}");
      $out = array_merge($out, MatchPageNames($o, $pats));
    }
    StopWatch("PageStore::ls end {$this->dirfmt}");
    return $out;
  }
}

function ReadPage($pagename, $since=0) {
  # read a page from the appropriate directories given by $WikiReadDirsFmt.
  global $WikiLibDirs,$Now;
  foreach ($WikiLibDirs as $dir) {
    $page = $dir->read($pagename, $since);
    if ($page) break;
  }
  if (@!$page) $page['ctime'] = $Now;
  if (@!$page['time']) $page['time'] = $Now;
  return $page;
}

function WritePage($pagename,$page) {
  global $WikiLibDirs,$WikiDir,$LastModFile;
  $WikiDir->iswrite = 1;
  for($i=0; $i<count($WikiLibDirs); $i++) {
    $wd = &$WikiLibDirs[$i];
    if ($wd->iswrite && $wd->exists($pagename)) break;
  }
  if ($i >= count($WikiLibDirs)) $wd = &$WikiDir;
  $wd->write($pagename,$page);
  if ($LastModFile && !@touch($LastModFile)) 
    { unlink($LastModFile); touch($LastModFile); fixperms($LastModFile); }
}

## fixperms attempts to correct permissions on a file or directory
## so that both PmWiki and the account (current dir) owner can manipulate it
function fixperms($fname, $add = 0) {
  clearstatcache();
  if (!file_exists($fname)) Abort('?no such file');
  $bp = 0;
  if (fileowner($fname)!=@fileowner('.')) $bp = (is_dir($fname)) ? 007 : 006;
  if (filegroup($fname)==@filegroup('.')) $bp <<= 3;
  $bp |= $add;
  if ($bp && (fileperms($fname) & $bp) != $bp)
    @chmod($fname,fileperms($fname)|$bp);
}

## CmpPageAttr is used with uksort to order a page's elements with
## the latest items first.  This can make some operations more efficient.
function CmpPageAttr($a, $b) {
  @list($x, $agmt) = explode(':', $a);
  @list($x, $bgmt) = explode(':', $b);
  if ($agmt != $bgmt) 
    return ($agmt==0 || $bgmt==0) ? $agmt - $bgmt : $bgmt - $agmt;
  return strcmp($a, $b);
}

/******************************************************************************
 *
 *           Following code is used to read the AINewsRanker's
 *            output and save them into PmWiki format
 *
 ****************************************************************************/

# Write Latest News
$filename = $PMWIKI_DIR."aaai/output/pmwiki_output.txt";
$handle = fopen($filename, "r");
$output = fread($handle, filesize($filename));
fclose($handle);

$pagename_result = "AITopics.AINews";
$page = ReadPage($pagename_result, READPAGE_CURRENT);
$page['text'] = $output;
WritePage($pagename_result, $page);
    
# Write Today News
$filename = $PMWIKI_DIR."aaai/output/pmwiki_output_norater.txt";
$handle = fopen($filename, "r");
$output = fread($handle, filesize($filename));
fclose($handle);

$today = date("Y-m-d");
$pagename_result = "AINewsFinder.$today-News";
$page = ReadPage($pagename_result, READPAGE_CURRENT);
$page['text'] = $output;
WritePage($pagename_result, $page);

# Add today news to AINewsFinder.NewsArchive page
$curr = date("Y-m-d G:i:s");
$archivepage = "AINewsFinder.NewsArchive";
$page = ReadPage($archivepage, READPAGE_CURRENT);
if (preg_match("/$curr/", $page['text']) == 0) {
	$page['text'] =  "[[".$pagename_result."|$curr AI News]][[<<]]\n".$page['text'];
	WritePage($archivepage, $page);
}

# Add today news to AITopics.NewsArchive page
$curr = date("M d");
$year = date("Y");
$archivepage = "AITopics.NewsArchive";
$page = ReadPage($archivepage, READPAGE_CURRENT);
$i = preg_match("/\'\'\'$year\'\'\'/", $page['text']);

if ($i == 0) {
    $pos = strpos($page['text'], "page.");
    $pretext = substr($page['text'], 0, $pos+7);
    $protext = substr($page['text'], $pos+7);
    $page['text'] =  $pretext."'''$year'''\n*[[".$pagename_result."|$curr]][[<<]]\n".$protext;
    WritePage($archivepage, $page);
}else{
    $pos = strpos($page['text'], "'''$year'''");
    $pretext = substr($page['text'], 0, $pos+11);
    $protext = substr($page['text'], $pos+11);
    $page['text'] =  $pretext."*[[".$pagename_result."|$curr]][[<<]]\n".$protext;
	WritePage($archivepage, $page);
}


# Add each news into AIArticles
$year = date("Y");
$file = $PMWIKI_DIR."aaai/output/urlids_output.txt";
$lines = file($file);
foreach($lines as $line_num => $id){
 
  $id = trim($id);
  $filename = $PMWIKI_DIR."aaai/output/aiarticles/".$id;
  $handle = fopen($filename, "r");
  $output = fread($handle, filesize($filename));
  fclose($handle);
  $pagename_result = "AIArticles.".$year."-".$id;
  $page = ReadPage($pagename_result, READPAGE_CURRENT);
  $page['text'] = $output;
  WritePage($pagename_result, $page);
  
}

?>
