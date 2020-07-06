import os
header = {'Authorization': 'Basic {}'.format(os.getenv("DATAESR_HEADER"))}
print(header)
