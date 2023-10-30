# PyMem - Get Memory Image on Windows
<h2>What is this ?</h2>
<p>It is a software that you can take "memory image with AFF4 format" from your device with Python.</p>
<h2>How is it working ?</h2>
<p>Before taking your memory copy, it obtains information about your memory size. Then, based on this information, it addresses your memory image according to the buffer size and buffer size, and then starts making memory copies of all your applications.</p>
<h2>Tested Image Forensic Softwares</h2>
<ul>
  <li>AccessData FTK Imager</li>
</ul>
<h2>Tested OS (on Virtual Machine)</h2>
<ul>
  <li>Windows 11 Build Number 22621.2283</li>
</ul>
<h2>Images</h2>
<img src="pic/ftk_imager_test.png" />
<br>
<img src="pic/wintest.png" />
<h2>Installation</h2>
<pre>
  ------------------------------------------------------------------------------------------------
  IMPORTANT : This program can CURRENTLY take a maximum of 2 GB memory image.
  ÖNEMLİ : Bu program ŞU ANLIK maksimum 2 GB bellek imajı alabilmektedir.
  ------------------------------------------------------------------------------------------------
  On CMD or PowerShell (Administrator)
  cd pymem_current_directory
  bcdedit /set testsigning on
  Check Memory Compression with "Get-MMAgent" command
  Disable Memory Compression with "Disable-MMAgent -mc" command
  Restart...
  
  winget install python --source=msstore
  OR
  winget install python
  python -m pip install -r requirements.txt
  python example.py
  NOTE : You must NEED Visual Studio C++ Libraries!!
  OR
  pip install pymem_snapshot (<a target="_blank" href="https://pypi.org/project/pymem-snapshot/">PyPi Link</a>)
  python example.py
</pre>
<h2>Disclaimer</h2>
<p>It should not be forgotten that taking a memory image is a serious process. In this process, you may encounter numerous errors, BSODs (Blue Screen of Death), and even memory errors. For this reason, we declare that we are not responsible for any damage that may arise.

For this reason, we recommend that you run your tests in demo environments.</p>
<p>Unutulmamalıdır ki, bellek imajı almak ciddi bir süreçtir. Bu süreçte çok sayıda hata, BSOD (Blue Screen of Death / Mavi Ekran Hataları) ve hatta bellek hatalarıyla karşılaşabilirsiniz. Bu nedenle doğabilecek herhangi bir zarardan sorumlu olmadığımızı beyan ederiz. 

Bu nedenle testlerinizi demo ortamlarda yapmanızı tavsiye ederiz.</p>
<h2>Links</h2>
<a target="_blank" href="https://pypi.org/project/pymem-snapshot/">PyPi Link</a>
<h2>Thanks</h2>
<b>Great thanks to the <a target="_blank" href="https://github.com/Velocidex/WinPmem">Velocidex (WinPMEM)</a> team for providing drivers</b>
