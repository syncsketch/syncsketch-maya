import datetime
import json
import os
import subprocess
import sys
from os.path import expanduser
from syncsketchGUI.lib import path
import logging
logger = logging.getLogger("syncsketchGUI")

# ======================================================================
# Module Functions

def get_creation_date(filename):
    if not os.path.isfile(filename):
        return str()
    
    mtime = os.path.getmtime(filename)
    creation_date = datetime.datetime.fromtimestamp(mtime)
    return str(creation_date.replace(microsecond = 0))



def probe(filename):
    if not filename:
        return
    
    ffmpeg_path = path.get_ffmpeg_bin() + '/'
    ffmpeg_path = path.sanitize(ffmpeg_path)
    filename = path.sanitize(filename)

    if sys.platform == 'win32':
        ffprobe_executable = 'ffprobe.exe'
    else:
        ffprobe_executable = 'ffprobe'

    ffprobe_command = '"{}{}" '.format(ffmpeg_path,ffprobe_executable)
    ffprobe_command += '-v error  '
    ffprobe_command += '-loglevel quiet  '
    ffprobe_command += '-select_streams v:0 '
    ffprobe_command += '-show_entries stream=width,height,avg_frame_rate,codec_name,duration '
    ffprobe_command += '-show_entries format=duration '
    ffprobe_command += '-of default=noprint_wrappers=1 '
    ffprobe_command += '-print_format json '
    ffprobe_command += ' "{}"'.format(filename)

    try:
        ffprobe_output = subprocess.check_output(ffprobe_command, shell = True).decode('utf-8')
        ffprobe_output = json.loads(ffprobe_output)
        return ffprobe_output
    
    except Exception as err:
        print (u'%s' %(err))
        return

def encodeToH264Mov(filepath = None, output_file = ""):
    ffmpeg_path = path.get_ffmpeg_bin() + '\\'

    if sys.platform == 'win32':
        filepath = path.make_windows_style(filepath)
        ffmpeg_executable = 'ffmpeg.exe'
        ffmpeg_path = os.path.join(ffmpeg_path, ffmpeg_executable)
        ffmpeg_path = path.make_windows_style(ffmpeg_path)
        output_file = path.make_windows_style(output_file)
    else:
        filepath = path.sanitize(filepath)
        ffmpeg_executable = 'ffmpeg'
        ffmpeg_path = os.path.join(ffmpeg_path, ffmpeg_executable)
        ffmpeg_path = path.sanitize(ffmpeg_path)
        output_file = path.sanitize(output_file)
    
    if not os.path.isfile(ffmpeg_path):
        logger.error("FFMPEG executable missing. No File at: {}".format(ffmpeg_path))
        raise RuntimeError("FFMPEG executable missing")

    filepath = filepath.replace("####", r"%04d")

    ffmpeg_command = [ffmpeg_path]
    ffmpeg_command.extend(['-i', filepath])
    # ffmpeg_command += '-filter:v select="eq(n\,0)" -vframes 1'
    ffmpeg_command.extend(['-c:v', 'libx264', '-preset', 'fast', '-tune', 'animation'])
    ffmpeg_command.extend(['-y'])
    ffmpeg_command.extend([output_file])
    logger.info('ffmpeg command: {}'.format(' '.join(ffmpeg_command)))
    try:
        subprocess.check_output(ffmpeg_command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        logger.error("FFMPEG conversion non zero exit: {}".format(err.output))
        raise err    


    # print "Creating Thumb for %s >> %s"%(filepath,output_file)
    if not os.path.isfile(output_file):
        logger.error("FFMPEG conversion from {} to {} not successful. Converted File missing. \n Command used: {}".format(filepath, output_file, ffmpeg_command))
        return
    else:
        return path.sanitize(output_file)


def get_thumb(filepath = None, output_file = ""):
    if not output_file:
        output_file = "{0}/Desktop/output_file.jpg".format(expanduser("~"))
   
    # should make this global
    ffmpeg_path = path.get_ffmpeg_bin() + '\\'

    if sys.platform == 'win32':
        ffmpeg_path = path.make_windows_style(ffmpeg_path)
        filepath = path.make_windows_style(filepath)
        ffmpeg_executable = 'ffmpeg.exe'
    else:
        ffmpeg_path = path.sanitize(ffmpeg_path)
        filepath = path.sanitize(filepath)
        ffmpeg_executable = 'ffmpeg'

    ffmpeg_command = '"{}{}" '.format(ffmpeg_path, ffmpeg_executable)
    ffmpeg_command += '-i "{}" '.format(filepath)
    # ffmpeg_command += '-filter:v select="eq(n\,0)" -vframes 1'
    ffmpeg_command += '-y '
    ffmpeg_command += '"{}"'.format(output_file)
    subprocess.call(ffmpeg_command, shell = True)
    output_file = path.sanitize(output_file)

    # print "Creating Thumb for %s >> %s"%(filepath,output_file)
    if not os.path.isfile(output_file):
        return
    else:
        return output_file
    '''
    ffmpeg -ss 01:23:45 -i input -vframes 1 -q:v 2 output.jpg

    
    if not filename:
        raise RuntimeError('Please specify a filename for the conversion.')
        
    if not output_file:
        output_file = filename.rsplit('.', 1)[0] + '.webm'
    
        print "Converting %s to webm format for faster upload..."%filename
        subprocess.call(ffmpeg_command, shell = True)
        output_file = path.sanitize(output_file)
        print output_file
    
        return output_file
    '''

def play_in_default_player(filename):
    filename = path.sanitize(filename)
    filename = path.make_safe(filename)

    get_thumb(filename)
    if sys.platform == 'win32':
        os.system('start {}'.format(filename))
    elif sys.platform == 'darwin':
        os.system('open {}'.format(filename))
    elif sys.platform == 'linux2':
        os.system('xdg-open {}'.format(filename))
    else:
        os.system('open {}'.format(filename))
