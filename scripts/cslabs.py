"""
Create CS labs.
"""
import django

django.setup()

from identification import CompSciLabs

reference_table = [
    { "abbr" : "NA",    "name" : "No Laboratory"                                        },
    { "abbr" : "ACL",   "name" : "Algorithms and Complexity Laboratory"                 },
    { "abbr" : "CSL",   "name" : "Computer Security Laboratory"                         },
    { "abbr" : "CVMIL", "name" : "Computer Vision and Machine Intelligence Laboratory"  },
    { "abbr" : "LCL",   "name" : "Logic and Computability Laboratory"                   },
    { "abbr" : "NDSL",  "name" : "Networks and Distributed Systems Laboratory"          },
    { "abbr" : "PCL",   "name" : "Parallel Computing Laboratory"                        },
    { "abbr" : "SCL",   "name" : "Scientific Computing Laboratory"                      },
    { "abbr" : "S3",    "name" : "Service Science and Software Engineering Laboratory"  },
    { "abbr" : "WSL",   "name" : "Web Science Laboratory"                               },
]

for lab in reference_table:
    CompSciLabs.objects.create(abbr=lab["abbr"], name=lab["name"]).save()

print("Finished running script:")
print(CompSciLabs.objects.values_list("abbr", flat=True))
