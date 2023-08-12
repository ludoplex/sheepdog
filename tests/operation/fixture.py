import os
import subprocess
import tempfile


def MakeZeroFile(nbSize):
    (fd, path) = tempfile.mkstemp()
    fh = os.fdopen(fd, "w")
    fh.truncate(nbSize)
    fh.close()
    return path


def MakeXFS(path):
    args = ["mkfs.xfs", "-ssize=4096", "-f", path]
    subprocess.check_output(args)
    return True


def MountLoopbackXFS(path, mnt):
    args = ["sudo", "mount", "-oloop,noatime", "-t", "xfs", path, mnt]
    subprocess.check_output(args)
    return True


def UnmountFS(mnt):
    args = ["sudo", "umount", mnt]
    subprocess.check_output(args)
    return True


def CreateSheepdogDisk(nbSize):
    img = MakeZeroFile(nbSize)
    try:
        MakeXFS(img)
    except:
        try:
            os.unlink(img)
        except:
            pass
        raise

    mnt = tempfile.mkdtemp()
    try:
        MountLoopbackXFS(img, mnt)
    except:
        try:
            os.rmdir(mnt)
            os.unlink(img)
        except:
            pass
        raise

    return (img, mnt)


def DestroySheepdogDisk(img, mnt):
    UnmountFS(mnt)
    os.rmdir(mnt)
    os.unlink(img)
    return True


def MakeDisksArg(disks):
    disksType = type(disks)
    if disksType == str:
        return disks
    return ",".join(disks) if disksType in (tuple, list) else None


def StartSheep(disks, port=None, zone=None, cluster=None):
    disksArg = MakeDisksArg(disks)
    if disksArg is None:
        raise ValueError
    cmd = ["sudo", "sheep"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    if zone is not None:
        cmd.extend(("--zone", str(zone)))
    cmd.extend(("--cluster", (cluster or "local"), disksArg))
    subprocess.check_output(cmd)
    return True


def KillLocalNode(port):
    cmd = ["dog", "node", "kill", "--local", "--port", str(port)]
    subprocess.check_output(cmd)
    return True


def ForceFormatCluster(copies, port=None):
    cmd = ["dog", "cluster", "format", "--force"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    cmd.extend(("--copies", str(copies)))
    subprocess.check_output(cmd)
    return True


def ShutdownCluster(port=None):
    cmd = ["dog", "cluster", "shutdown"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    subprocess.check_output(cmd)
    return True


def CreateVDI(name, nb_size=4194304, prealloc=False, port=None):
    cmd = ["dog", "vdi", "create"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    if prealloc:
        cmd.append("--prealloc")
    cmd.extend((name, str(nb_size)))
    subprocess.check_output(cmd)
    return True


def DeleteVDI(name, tag=None, port=None):
    cmd = ["dog", "vdi", "delete"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    if tag is not None:
        cmd.extend(("--snapshot", tag))
    cmd.append(name)
    subprocess.check_output(cmd)
    return True


def ListVDI(port=None):
    cmd = ["dog", "vdi", "list", "--raw"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    out = subprocess.check_output(cmd)
    if len(out) == 0:
        return []

    vdis = []
    for s in out.rstrip("\n").split("\n"):
        c = s.split(" ")
        v = {"snapshot": (c[0] == "s"),
             "cloned": (c[0] == "c"),
             "name": c[1],
             "nb_size": int(c[3]),
             "vdi_id": int(c[7], 16),
             "copies": int(c[8]),
             "tag": c[9],
             "block_size_shift": int(c[10])}
        vdis.append(v)

    return vdis


def WriteVDI(name, content, port=None):
    cmd = ["dog", "vdi", "write"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    cmd.append(name)

    dog = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    dog.communicate(input=content)
    if dog.returncode != 0:
        raise CalledProcessError(dog.returncode)

    return True


def ReadVDI(name, tag=None, offset=None, length=None, port=None):
    cmd = ["dog", "vdi", "read"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    if tag is not None:
        cmd.extend(("--snapshot", tag))
    cmd.append(name)
    if offset is not None:
        cmd.append(str(offset))
        if length is not None:
            cmd.append(str(length))
    return subprocess.check_output(cmd)


def SnapshotVDI(name, tag, port=None):
    cmd = ["dog", "vdi", "snapshot"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    cmd.extend(("--snapshot", tag, name))
    subprocess.check_output(cmd)
    return True


def CloneVDI(src, tag, dst, port=None):
    cmd = ["dog", "vdi", "clone"]
    if port is not None:
        cmd.extend(("--port", str(port)))
    cmd.extend(("--snapshot", tag, src, dst))
    subprocess.check_output(cmd)
    return True

def GetObjFileName(directory):
    obj_dir = f"{directory}/obj"
    cmd = ["ls", obj_dir]
    rslt = (subprocess.check_output(cmd)).split('\n')
    rslt.remove('')
    return rslt

def FindObjFileName(disks, file_name):
    cmd = ["find"]
    cmd.extend(mnt for img, mnt in disks)
    cmd.extend(("-type", "f", "-name", file_name))
    rslt = (subprocess.check_output(cmd)).split('\n')
    rslt.remove('')
    return rslt

def GetMd5(file_path):
    cmd = ["md5sum", file_path]
    rslt_list = (subprocess.check_output(cmd)).split()
    return rslt_list[0]
