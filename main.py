import ftplib, os, datetime
from logger import run_and_log


class Dir:
    def __init__(self, name:str, path:str) -> None:
        self.files:list = []
        self.dirs:list = []
        self.name:str = name
        self.path:str = path
    
    def __gt__(self, comp):
        return self.name > comp.name
    
    def __lt__(self, comp):
        return self.name < comp.name
    
    def __ge__(self, comp):
        return self.name >= comp.name
    
    def __le__(self, comp):
        return self.name <= comp.name
    
    def __eq__(self, comp):
        return self.name == comp.name

    def __repr__(self)->str:
        return self.name
    

class SyncApp:
    def __init__(self, sync_path_mobile:str, sync_path_pc:str):
        print("---------------------------------------------------------")
        print(datetime.datetime.now())
        print("---------------------------------------------------------")

        self.server = ftplib.FTP()
        self.server.connect('192.168.1.111', 2221)
        self.server.login('ftp','ftp')
        self.server.cwd(sync_path_mobile)

        self.mobile_dir = Dir("7th sem", sync_path_mobile)
        self.initialize_mobile_dir(self.mobile_dir)            
        self.server.cwd(sync_path_mobile)

        self.pc_dir = self.initialize_pc_dir(sync_path_pc)

    def initialize_mobile_dir(self, obj:Dir):
        self.server.cwd(obj.path)
        for i in self.server.mlsd(facts=["type"]):
            if i[1]["type"] == "file":
                obj.files.append(Dir(i[0], obj.path+"/"+i[0]))

            elif i[1]["type"] == "dir":
                obj.dirs.append(Dir(i[0], obj.path+"/"+i[0]))
                self.initialize_mobile_dir(obj.dirs[-1])


    def copy_file_to_pc(self, copy_file, copy_path):
        """
        copy_file is name only\n
        copy_path is full_path
        """
        file = os.path.join(copy_path, copy_file)
        if not os.path.exists(file):
            with open(os.path.join(copy_path, copy_file), "wb") as f:
                print(f"Copying {copy_file} to '{copy_path}'...", end=" ")
                self.server.retrbinary("RETR "+ copy_file, f.write)
                print(f"Complete!!")

    def copy_file_to_phone(self, file_path):
        """
        file_path is full path
        """
        with open(file_path, "rb") as f:
            print(f"Copying '{file_path}' to '{self.server.pwd()}'...", end=" ")
            self.server.storbinary("STOR "+os.path.basename(file_path), f)
            print("Complete")


    def copy_folder_to_mobile(self, path):
        """
        path is full path
        """
        print(f"Upload folder = '{path}'")
        folder_name = os.path.basename(path)
        print(f"Creating '{folder_name}' in '{self.server.pwd()}'")
        self.server.mkd(folder_name)
        print(f"Changing current dir to '{folder_name}'")
        self.server.cwd(folder_name)
        # return
        for name in os.listdir(path):
            local_path = os.path.join(path, name)

            if os.path.isfile(local_path):
                self.copy_file_to_phone(local_path)

            elif os.path.isdir(local_path):
                self.copy_folder_to_mobile(local_path)
                print('Changing back to parent directory...')
                self.server.cwd('..')            


    def download_folder(self, source_folder, destination_folder):
        contents = []
        self.server.retrlines("NLST {}".format(source_folder), contents.append)
        
        for item in contents:
            source_item_path = "{}/{}".format(source_folder, item)
            destination_item_path = os.path.join(destination_folder, item)
            if "." in item:
                print(f"Copying '{source_item_path}' to '{destination_item_path}'...", end=" ")
                with open(destination_item_path, "wb") as local_file:
                    self.server.retrbinary("RETR {}".format(source_item_path), local_file.write)
                print("Complete!!")
            else:  # If it's a subfolder
                print(f"Creating folder '{destination_item_path}'...")
                os.makedirs(destination_item_path)
                self.download_folder(source_item_path, destination_item_path)


    def copy_folder_to_pc(self, source_folder, destination_path):
        """
        source_folder is just name\n
        destination_path is full path
        """
        new_destination = os.path.join(destination_path, source_folder)
        os.makedirs(new_destination)
        self.download_folder(source_folder, new_destination)


    def initialize_pc_dir(self, path):
        dir = Dir(os.path.basename(path), path)

        # Get the list of files and subdirectories in the path
        contents = os.listdir(path)

        contents = os.listdir(dir.path)
        for item in contents:
            item_path = os.path.join(dir.path, item)
            if os.path.isfile(item_path):
                dir.files.append(Dir(os.path.basename(item), item))
            elif os.path.isdir(item_path):
                dir.dirs.append(self.initialize_pc_dir(item_path))
        
        return dir


    def compare(self, mobile_data:list[Dir], pc_data:list[Dir]):
        mobile_data_set_name = set([i.name for i in mobile_data])
        pc_data_set_name = set([j.name for j in pc_data])

        moblie_only_name = mobile_data_set_name-pc_data_set_name
        mobile_only_data = []

        for data in mobile_data:
            if data.name in moblie_only_name:
                mobile_only_data.append(data)

        pc_only_name = pc_data_set_name-mobile_data_set_name
        pc_only_data = []

        for data in pc_data:
            if data.name in pc_only_name:
                pc_only_data.append(data)
        
        both_name = mobile_data_set_name.intersection(pc_data_set_name)
        both_data = {"mobile":[],"pc":[]}

        for data in mobile_data:
            if data.name in both_name:
                both_data["mobile"].append(data)
        
        for data in pc_data:
            if data.name in both_name:
                both_data["pc"].append(data)
        

        return mobile_only_data, pc_only_data, both_data


    def copy_checker(self, moblie:Dir=None, pc:Dir=None):
        """
        prints the files that are to be copied without acutally copying them
        """
        if not mobile:
            mobile = self.mobile_dir
        if not pc:
            pc = self.pc_dir

        copy_to_pc, copy_to_mobile, recurse_list = self.compare(moblie.dirs, pc.dirs)
        copy_to_pc_file, copy_to_mobile_file, recurse_list_file = self.compare(moblie.files, pc.files)

        print("Copy to mobile folders: "+", ".join(i.name for i in copy_to_mobile))
        print("Copy to mobile files: "+", ".join(i.name for i in copy_to_mobile_file))

        print("Copy to pc folders: "+", ".join(i.name for i in copy_to_pc))
        print("Copy to pc files: "+", ".join(i.name for i in copy_to_pc_file))

        print("\n")
        print("Recurse: "+", ".join(i for i in recurse_list))
        for i,j in zip(sorted(recurse_list["mobile"]), sorted(recurse_list["pc"])):
            print(f"Folder Name = {i}")
            self.copy_checker(i, j)


    def sync(self, mobile_dir:Dir=None, pc_dir:Dir=None):
        if not mobile_dir:
            mobile_dir = self.mobile_dir
        if not pc_dir:
            pc_dir = self.pc_dir

        copy_to_pc, copy_to_mobile, recurse_list = self.compare(mobile_dir.dirs, pc_dir.dirs)
        copy_to_pc_file, copy_to_mobile_file, recurse_list_file = self.compare(mobile_dir.files, pc_dir.files)

        cur_dir = self.server.pwd()
        self.server.cwd(mobile_dir.path)
        if copy_to_mobile != []:
            print(f"Copy to mobile folders: from '{pc_dir.path}' to '{mobile_dir.path}' \n\t"+", ".join(i.name for i in copy_to_mobile))
            for i in copy_to_mobile:
                self.copy_folder_to_mobile(i.path)
                self.server.cwd(mobile_dir.path)
        if copy_to_mobile_file!=[]:
            print(f"Copy to mobile files:  from '{pc_dir.path}' to '{mobile_dir.path}' \n\t"+", ".join(i.name for i in copy_to_mobile_file))
            for i in copy_to_mobile_file:
                self.copy_file_to_phone(os.path.join(pc_dir.path, i.name))
        self.server.cwd(mobile_dir.path)
        if copy_to_pc != []:
            print(f"Copy to pc folders:  from '{mobile_dir.path}' to '{pc_dir.path}'  \n\t"+", ".join(i.name for i in copy_to_pc))
            for i in copy_to_pc:
                self.copy_folder_to_pc(i.name, pc_dir.path)
                self.server.cwd(mobile_dir.path)
        if copy_to_pc_file!=[]:
            print(f"Copy to pc files:  from '{mobile_dir.path}' to '{pc_dir.path}' \n\t"+", ".join(i.name for i in copy_to_pc_file))
            for i in copy_to_pc_file:
                self.copy_file_to_pc(i.name, pc_dir.path)
        self.server.cwd(cur_dir)

        print("\n")
        print("Recurse: "+", ".join(i for i in recurse_list))
        for i,j in zip(sorted(recurse_list["mobile"]), sorted(recurse_list["pc"])):
            print(f"Folder Name = {i}")
            self.sync(mobile_dir=i, pc_dir=j)


if __name__ == "__main__":
    def main():
        sync_path_mobile = "/pul076bce100/7th sem"
        sync_path_pc = "D:/7th sem"

        app = SyncApp(sync_path_mobile, sync_path_pc)
        # app.copy_checker(app.mobile_dir, app.pc_dir)
        app.sync()
    
    run_and_log(main, "log.txt")
    print("Complete!!")
