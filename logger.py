import sys


class DualOutput:
    def __init__(self, original, log):
        self.original = original
        self.log = log

    def write(self, message):
        self.original.write(message)
        self.log.write(message)

    def flush(self):
        self.original.flush()
        self.log.flush()
        

def run_and_log(function, log_file_path:str):
    """
    pass a function to run while logging the print statements\n
    log_file_path: is the file to be use for logging\n
    always appends the logfile
    """
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    log_file = open(log_file_path, "a")

    dual_output = DualOutput(original_stdout, log_file)
    dual_stderr = DualOutput(original_stderr, log_file)
    sys.stdout = dual_output
    sys.stderr = dual_stderr

    function()

    sys.stdout.flush()
    sys.stderr.flush()
    log_file.flush()
    log_file.close()
    
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    
    log_file.close()