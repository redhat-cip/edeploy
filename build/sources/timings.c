/*
 * timings.c by CyrIng
 *
 * Copyright (C) 2012 CYRIL INGENIERIE
 * Licenses: GPL2
 *
 * Version [0.2.1]
 *
 * Readings & Specifications :
 * 1-	Memtest86++ v4.20 @ http://www.memtest.org
 * 2-	Linux kernel release 3 @ http://kernel.org
 * 3-	Intel® CoreTM i7-800 and i5-700 Desktop Processor Series Datasheet – Volume 2
 * 4-	Micron Technology, Inc. TN-41-07: DDR3 Power-Up, Initialization, and Reset
 */

#include <stdio.h>
// #include <sys/io.h>
#include <unistd.h>

#define PCI_CONFIG_ADDRESS(bus, dev, fn, reg) \
	(0x80000000 | (bus << 16) | (dev << 11) | (fn << 8) | (reg & ~3))

#define BUILDIO(bwl, bw, type)						\
static inline void out##bwl(unsigned type value, int port)		\
{									\
	asm volatile("out" #bwl " %" #bw "0, %w1"			\
		     : : "a"(value), "Nd"(port));			\
}									\
									\
static inline unsigned type in##bwl(int port)				\
{									\
	unsigned type value;						\
	asm volatile("in" #bwl " %w1, %" #bw "0"			\
		     : "=a"(value) : "Nd"(port));			\
	return value;							\
}									\

BUILDIO(b, b, char) BUILDIO(w, w, short) BUILDIO(l,, int)

int main(int argc, char *argv[])
{
    int i, PRINT_REGISTERS = 0, PRINT_TIMINGS = 1, PRINT_SPD =
	0, PRINT_HELP = 0;
    unsigned bus = 0xff, dev = 0x4, func = 0;

    if (argc > 1)
	for (i = 1; i < argc; i++)
	    if (argv[i][0] == '-' || argv[i][0] == '~')
		switch (argv[i][1]) {
		case 'b':
		    if (argv[i + 1])
			bus = atoi(argv[++i]);
		    else
			PRINT_HELP = 1;
		    break;
		case 'd':
		    if (argv[i + 1])
			dev = atoi(argv[++i]);
		    else
			PRINT_HELP = 1;
		    break;
		case 'f':
		    if (argv[i + 1])
			func = atoi(argv[++i]);
		    else
			PRINT_HELP = 1;
		    break;
		case 'r':
		    PRINT_REGISTERS = (argv[i][0] == '~') ? 0 : 1;
		    break;
		case 't':
		    PRINT_TIMINGS = (argv[i][0] == '~') ? 0 : 1;
		    break;
		case 's':
		    PRINT_SPD = (argv[i][0] == '~') ? 0 : 1;
		    break;
		case 'h':
		default:
		    PRINT_HELP = 1;
		    break;
	    } else
		PRINT_HELP = 1;

    if (!PRINT_HELP) {
	if (!geteuid() && !iopl(3))	// Set I/O privilege to level 3 to unlock access to PCI configuration
	{
	    int MRs = 0, RANK_TIMING_B = 0, BANK_TIMING =
		0, REFRESH_TIMING = 0, tCL = 0, tRCD = 0, tRP = 0, tRAS =
		0, tRRD = 0, tRFC = 0, tWR = 0, tWTPr = 0, tRTPr =
		0, tFAW = 0, B2B = 0;
	    int code, channelCount = 0;
	    char *confChanStr[] = { "Zero", "Single", "Dual", "Triple" };

	    printf("Ready to Request I/O in PCI device %x:%u.%u\n\n", bus,
		   dev, func);
/*	    printf
		("This is an experimental code !\tinline I/O functions:YES\n\n"
		 "Last chance to interrupt with [Ctrl]+[c] or [Return] to continue\n");
	    getchar();
*/
	    outl(PCI_CONFIG_ADDRESS(bus, 3, 0, 0x48), 0xcf8);
	    code = inw(0xcfc + (0x48 & 2));
	    code = (code >> 8) & 0x7;
	    channelCount =
		(code == 7 ? 3 : code == 4 ? 1 : code == 2 ? 1 : code ==
		 1 ? 1 : 2);
	    printf("IMC %x:3.0 Memory Controler is a %s(%d) Channel.\n\n",
		   bus, confChanStr[channelCount], code);

	    printf
		("DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B   \n");
	    for (i = 0; i < channelCount; i++) {
		outl(PCI_CONFIG_ADDRESS(bus, dev + i, func, 0x70), 0xcf8);
		MRs = inl(0xcfc);
		outl(PCI_CONFIG_ADDRESS(bus, dev + i, func, 0x84), 0xcf8);
		RANK_TIMING_B = inl(0xcfc);
		outl(PCI_CONFIG_ADDRESS(bus, dev + i, func, 0x88), 0xcf8);
		BANK_TIMING = inl(0xcfc);
		outl(PCI_CONFIG_ADDRESS(bus, dev + i, func, 0x8c), 0xcf8);
		REFRESH_TIMING = inl(0xcfc);

		tCL = ((MRs >> 4) & 0x7);
		if (tCL != 0)
		    tCL += 4;
		tRCD = (BANK_TIMING & 0x1E00) >> 9;
		tRP = (BANK_TIMING & 0xF);
		tRAS = (BANK_TIMING & 0x1F0) >> 4;
		tRRD = (RANK_TIMING_B & 0x1c0) >> 6;
		tRFC = (REFRESH_TIMING & 0x1ff);
		tWR = ((MRs >> 9) & 0x7);
		if (tWR != 0)
		    tWR += 4;
		tWTPr = (BANK_TIMING & 0x3E0000) >> 17;
		tRTPr = (BANK_TIMING & 0x1E000) >> 13;
		tFAW = (RANK_TIMING_B & 0x3f);
		B2B = (RANK_TIMING_B & 0x1f0000) >> 16;

		if (PRINT_TIMINGS)
		    printf(" #%1i |%4d%6d%6d%6d%6d%6d%6d%6d%6d%6d%6d\n",
			   i, tCL, tRCD, tRP, tRAS, tRRD, tRFC, tWR, tWTPr,
			   tRTPr, tFAW, B2B);
		if (PRINT_REGISTERS) {
		    printf
			("    |\tMC_CHANNEL_%1i_RANK_TIMING_B  [0x%08x]\n",
			 i, RANK_TIMING_B);
		    printf
			("    |\tMC_CHANNEL_%1i_BANK_TIMING    [0x%08x]\n",
			 i, BANK_TIMING);
		    printf
			("    |\tMC_CHANNEL_%1i_REFRESH_TIMING [0x%08x]\n",
			 i, REFRESH_TIMING);
		    printf
			("    |\tMC_CHANNEL_%1i_MRS_VALUES     [0x%08x]\n",
			 i, MRs);
		}
	    }
//                      unsigned short SMBUS_ADDR=0x0;
//                      outl(PCI_CONFIG_ADDRESS(0x0, 0x0, 0, 0x20), 0xcf8);
//                      SMBUS_ADDR=inw(0xcfc);

	    if (PRINT_SPD) {
		printf("\nSPD: not implemented yet !\n");
/*
				int j;
				for(j=0;j<32;j++)
					for(i;i<8;i++)
					{
						outl(PCI_CONFIG_ADDRESS(0,j,i,0), 0xcf8);
						SMBUS_ADDR=inw(0xcfe);
				printf("\nSMBUS CONTROLLER [0x%08x]\n", SMBUS_ADDR);
					}
//				printf("\nSMBUS BASE ADDRESS [0x%08x]\n", SMBUS_ADDR);
*/
	    }

	    iopl(0);		// Back to normal I/O privilege
	} else
	    printf("%s: Must be root !\n", argv[0]);
    } else
	printf("Usage: %s [OPTION]\n"
	       "-r / ~r         print / hide raw register values\n"
	       "-t / ~t         print / hide timings (default)\n"
	       "-s / ~s         print / hide SPD\n"
	       "-b <num>        use the specified bus id\n"
	       "-d <num>        use the specified device id\n"
	       "-f <num>        use the specified function number\n"
	       "-h              give this help list\n", argv[0]);
    return (!PRINT_HELP ? 0 : -1);
}
