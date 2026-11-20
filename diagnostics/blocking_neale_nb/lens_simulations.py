                                                                                                                      
'''
    LISTS LENS SET SIMULATIONS NAMES
'''

import sys

def get_ens_set_names(ens_name,num_ens):
    
    match(ens_name):
    
        case "CESM1":
            
            lens_sims0 = [
                "b.e11.B20TRC5CNBDRD.f09_g16.001",
                "b.e11.B20TRC5CNBDRD.f09_g16.002",
                "b.e11.B20TRC5CNBDRD.f09_g16.003",
                "b.e11.B20TRC5CNBDRD.f09_g16.004",
                "b.e11.B20TRC5CNBDRD.f09_g16.005",
                "b.e11.B20TRC5CNBDRD.f09_g16.006",
                "b.e11.B20TRC5CNBDRD.f09_g16.007",
                "b.e11.B20TRC5CNBDRD.f09_g16.008",
                "b.e11.B20TRC5CNBDRD.f09_g16.009",
                "b.e11.B20TRC5CNBDRD.f09_g16.010",
                "b.e11.B20TRC5CNBDRD.f09_g16.011",
                "b.e11.B20TRC5CNBDRD.f09_g16.012",
                "b.e11.B20TRC5CNBDRD.f09_g16.013",
                "b.e11.B20TRC5CNBDRD.f09_g16.014",
                "b.e11.B20TRC5CNBDRD.f09_g16.015",
                "b.e11.B20TRC5CNBDRD.f09_g16.016",
                "b.e11.B20TRC5CNBDRD.f09_g16.017",
                "b.e11.B20TRC5CNBDRD.f09_g16.018",
                "b.e11.B20TRC5CNBDRD.f09_g16.019",
                "b.e11.B20TRC5CNBDRD.f09_g16.020",
                "b.e11.B20TRC5CNBDRD.f09_g16.021",
                "b.e11.B20TRC5CNBDRD.f09_g16.022",
                "b.e11.B20TRC5CNBDRD.f09_g16.023",
                "b.e11.B20TRC5CNBDRD.f09_g16.024",
                "b.e11.B20TRC5CNBDRD.f09_g16.025",
                "b.e11.B20TRC5CNBDRD.f09_g16.026",
                "b.e11.B20TRC5CNBDRD.f09_g16.027",
                "b.e11.B20TRC5CNBDRD.f09_g16.028",
                "b.e11.B20TRC5CNBDRD.f09_g16.029",
                "b.e11.B20TRC5CNBDRD.f09_g16.030",
                "b.e11.B20TRC5CNBDRD.f09_g16.031",
                "b.e11.B20TRC5CNBDRD.f09_g16.032",
                "b.e11.B20TRC5CNBDRD.f09_g16.033",
                "b.e11.B20TRC5CNBDRD.f09_g16.034",
                "b.e11.B20TRC5CNBDRD.f09_g16.035",
                "b.e11.B20TRC5CNBDRD.f09_g16.101",
                "b.e11.B20TRC5CNBDRD.f09_g16.102",
                "b.e11.B20TRC5CNBDRD.f09_g16.103",
                "b.e11.B20TRC5CNBDRD.f09_g16.104",
                "b.e11.B20TRC5CNBDRD.f09_g16.105",
                "b.e11.B20TRC5CNBDRD.f09_g16.106",
                "b.e11.B20TRC5CNBDRD.f09_g16.107"
            ] 

        case "CESM1-LE-RCP85":
            
            lens_sims0 = [                                                                                                   
                "b.e11.RCP85C5CNBDRD.f09_g16.001",     
                "b.e11.RCP85C5CNBDRD.f09_g16.008",
                "b.e11.RCP85C5CNBDRD.f09_g16.009",
                "b.e11.RCP85C5CNBDRD.f09_g16.010",
                "b.e11.RCP85C5CNBDRD.f09_g16.011",
                "b.e11.RCP85C5CNBDRD.f09_g16.012",
                "b.e11.RCP85C5CNBDRD.f09_g16.013",
                "b.e11.RCP85C5CNBDRD.f09_g16.014",
                "b.e11.RCP85C5CNBDRD.f09_g16.015",
                "b.e11.RCP85C5CNBDRD.f09_g16.016",
                "b.e11.RCP85C5CNBDRD.f09_g16.017",
                "b.e11.RCP85C5CNBDRD.f09_g16.018",
                "b.e11.RCP85C5CNBDRD.f09_g16.019",
                "b.e11.RCP85C5CNBDRD.f09_g16.020",
                "b.e11.RCP85C5CNBDRD.f09_g16.021",
                "b.e11.RCP85C5CNBDRD.f09_g16.022",
                "b.e11.RCP85C5CNBDRD.f09_g16.023",
                "b.e11.RCP85C5CNBDRD.f09_g16.024",
                "b.e11.RCP85C5CNBDRD.f09_g16.025",
                "b.e11.RCP85C5CNBDRD.f09_g16.026",
                "b.e11.RCP85C5CNBDRD.f09_g16.027",
                "b.e11.RCP85C5CNBDRD.f09_g16.028",
                "b.e11.RCP85C5CNBDRD.f09_g16.029",
                "b.e11.RCP85C5CNBDRD.f09_g16.030",
                "b.e11.RCP85C5CNBDRD.f09_g16.031",
                "b.e11.RCP85C5CNBDRD.f09_g16.032",
                "b.e11.RCP85C5CNBDRD.f09_g16.033",
                "b.e11.RCP85C5CNBDRD.f09_g16.034",
                "b.e11.RCP85C5CNBDRD.f09_g16.035",
                "b.e11.RCP85C5CNBDRD.f09_g16.101",
                "b.e11.RCP85C5CNBDRD.f09_g16.102",
                "b.e11.RCP85C5CNBDRD.f09_g16.103",
                "b.e11.RCP85C5CNBDRD.f09_g16.104",
                "b.e11.RCP85C5CNBDRD.f09_g16.105",
                "b.e11.RCP85C5CNBDRD.f09_g16.106",
                "b.e11.RCP85C5CNBDRD.f09_g16.107"                                                                                
            ]                                                                                                              
                                                                                                                     
                                                                                                                        
        case "CESM2":  
         
            lens_sims0 = [                                                             
                "b.e21.BHISTcmip6.f09_g17.LE2-1001.001",
                "b.e21.BHISTcmip6.f09_g17.LE2-1021.002",
                "b.e21.BHISTcmip6.f09_g17.LE2-1041.003",
                "b.e21.BHISTcmip6.f09_g17.LE2-1061.004",
                "b.e21.BHISTcmip6.f09_g17.LE2-1081.005",
                "b.e21.BHISTcmip6.f09_g17.LE2-1101.006",
                "b.e21.BHISTcmip6.f09_g17.LE2-1121.007",  
                "b.e21.BHISTcmip6.f09_g17.LE2-1141.008",  
                "b.e21.BHISTcmip6.f09_g17.LE2-1161.009",
                "b.e21.BHISTcmip6.f09_g17.LE2-1181.010",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.001",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.002",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.003",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.004",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.005",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.006",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.007",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.008",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.009",
                "b.e21.BHISTcmip6.f09_g17.LE2-1231.010",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.001",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.002",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.003",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.004",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.005",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.006",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.007",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.008",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.009",
                "b.e21.BHISTcmip6.f09_g17.LE2-1251.010",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.001",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.002",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.003",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.004",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.005",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.006",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.007",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.008",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.009",
                "b.e21.BHISTcmip6.f09_g17.LE2-1281.010",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.001",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.002",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.003",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.004",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.005",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.006",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.007",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.008",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.009",
                "b.e21.BHISTcmip6.f09_g17.LE2-1301.010"                                                                          
            ]                                                                                                               

        case "CAM6":                                                                                     
            lens_sims0 = [
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens01",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens02",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens03",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens04",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens05",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens06",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens07",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens08",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens09",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens09",
                "f.e21.FHIST_BGC.f09_f09.historical.ersstv5.goga.ens10"
            ]
            
    
        case "E3SMv1":                                                                                     
            lens_sims0 = [  
                "20180215.DECKv1b_H1.ne30_oEC.edison",  
                "20180220.DECKv1b_H2.ne30_oEC.edison",
                "20180302.DECKv1b_H3.ne30_oEC.edison",                                                                      
                "20180305.DECKv1b_H4.ne30_oEC.edison",   
                "20180307.DECKv1b_H5.ne30_oEC.edison"
            ]                                                                                                            
                                                                                                                      
        case "E3SMv2":                                                                                     
            lens_sims0 = [                                                                                                  
                "v2.FV1.historical_0101",               
                "v2.FV1.historical_0111",                                                                                       
                "v2.FV1.historical_0121",                                                                                       
                "v2.FV1.historical_0131",                                                                                       
                "v2.FV1.historical_0141",                                                                                       
                "v2.FV1.historical_0151",                                                                                       
                "v2.FV1.historical_0161",                                                                                       
                "v2.FV1.historical_0171",                                                                                       
                "v2.FV1.historical_0181",                                                                                       
                "v2.FV1.historical_0191",                                                                                       
                "v2.FV1.historical_0201",                                                                                       
                "v2.FV1.historical_0211",                                                                                       
                "v2.FV1.historical_0221",                                                                                       
                "v2.FV1.historical_0231",                                                                                       
                "v2.FV1.historical_0241",                                                                                       
                "v2.FV1.historical_0251",
                "v2.FV1.historical_0261",
                "v2.FV1.historical_0271",                                                                                       
                "v2.FV1.historical_0281",                                                                                       
                "v2.FV1.historical_0301"                                                                                        
            ]

        case "EAMv2":                                                                                     
           lens_sims0 = [                 
                "v2.FV1.AMIP20TR_0111",
                "v2.FV1.AMIP20TR_0121",
                "v2.FV1.AMIP20TR_0131",
                "v2.FV1.AMIP20TR_0141",
                "v2.FV1.AMIP20TR_0161",
                "v2.FV1.AMIP20TR_0171",
                "v2.FV1.AMIP20TR_0181",
                "v2.FV1.AMIP20TR_0191",
                "v2.FV1.AMIP20TR_0211",
                "v2.FV1.AMIP20TR_0221"
           ]    

        case _:
            print(' ')
            print(ens_name,' is not a recognized ensemble set - exiting...')
            print(' ')
            sys.exit(0)
            

# Subset for requested ensemble numbers

    num_ens_all = len(lens_sims0)
    lens_sims = lens_sims0[0:num_ens]

# info

    print(' ')
    print('++ Large ensemble = ',ens_name,': ',num_ens,' out of ',num_ens_all,' total (first/last) ++')
    print(lens_sims[0])
    print(lens_sims[-1])



    
    return lens_sims