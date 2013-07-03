<?php
require_once("../config.inc.php");
session_start();
if (!isset($_SESSION['acct_manager']))
  $_SESSION['acct_manager']= new RODSAcctManager();

$ruri="";
if (isset($_REQUEST['ruri']))
  $ruri=$_REQUEST['ruri'];
else
{
  $response=array('success'=> false,'errmsg'=>'Expected RODS URI not found');
  echo json_encode($response);
  exit(0);
} 

$files=array();
$dirs=array();
if (isset($_REQUEST['files']))
  $files=$_REQUEST['files'];
if (isset($_REQUEST['dirs']))
  $dirs=$_REQUEST['dirs'];

if ( (empty($files))&&(empty($dirs)) )
{
  $response=array('success'=> false,'errmsg'=>'No files or collections specified');
  echo json_encode($response);
  exit(0);
}  

try {
  $parent=ProdsDir::fromURI($ruri, false);
  if (empty($parent->account->pass))
  {
    $acct=$_SESSION['acct_manager']->findAcct($parent->account);
    if (empty($acct))
    {
      $response=array('success'=> false,'errmsg'=>'Authentication Required');
      echo json_encode($response);
      exit(0);
    }
    $parent->account=$acct;
  }
  if (empty($parent->account->zone))
  {
    $parent->account->getUserInfo();
  }  
  
  // prepare download task file
  $taskdir = '/tmp/ida_downloads/';
  $iget = '/opt/iRODS/iRODS_3.2/clients/icommands/bin/iget -V';
  $timestamp = date('Ymd-His', time());
  $user = $parent->account->user;
  $tmpfilename = $taskdir.'tmp_'.$timestamp.'_'.$user.'.sh';
  $taskfilename = $taskdir.'download_'.$timestamp.'_'.$user.'.sh';
  $dstdir = '/mnt/FROM_IDA/'.$user;
  
  $tmpfile = fopen($tmpfilename,'w');

  $files = array_unique($files);
  $num_files=0;
  foreach ($files as $filename)
  {
    if (strlen($filename)>0)
    {
      //$myfile=new ProdsFile($parent->account,$parent->path_str.'/'.$filename);
      fwrite($tmpfile, $iget.' "'.$parent->path_str.'/'.$filename.'" '.$dstdir."\n");
      $num_files++;
    }
  }
  
  $dirs = array_unique($dirs);
  $num_dirs=0;
  foreach ($dirs as $dirname)
  {
    if (strlen($dirname)>0)
    {
      //$mydir=new ProdsDir($parent->account,$parent->path_str.'/'.$dirname);
      fwrite($tmpfile, 'iget -v -r "'.$parent->path_str.'/'.$dirname.'" '.$dstdir."\n");
      $num_dirs++;
    }
  }

  // close tmp file and rename to task file  
  fclose($tmpfile);
  chmod($tmpfilename,0555);
  rename($tmpfilename,$taskfilename);

  $addir = str_replace('/mnt','LMU2/users',$dstdir);
  $response=array('success'=> false,'log'=>"This is not an error. $num_files files and $num_dirs collections are scheduled for downloading to ".$addir.". You will be notified by email when the download is completed.");
  echo json_encode($response);
  
} catch (Exception $e) {
  $response=array('success'=> false,'errmsg'=> $e->getMessage(), 'errcode'=> $e->getCode());
  echo json_encode($response);
}

  
?>
