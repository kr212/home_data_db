def b_to_f(dane):
#float zapisany zgodnie z IEEE754
#mamy 32 bity: 31 - znak +-, 31-23 wykładnik potęgi, 22-0 to wartość
#bajty są po kolei w dane - dane[0] to najstarszy bajt
	#print(f'b_to_f {dane[0]} {dane[1]} {dane[2]} {dane[3]}')
#wyciągam znak liczby z bitu 7 najstarszego bajtu (0 - dodatni 1 - ujemny
	znak=dane[0] >> 7
#wykłdanik - trzeba przesunąć wszystko jakby o 1 w lewo i odjąc 127 - to jest ze specyfikacji
	wykladnik=((dane[0] << 1) | (dane[1] >> 7)) - 127
	
#do mantysy dodaje się zawsze najstarszy bit 1 bo to wynika ze specyfikacji
	mantysa=float((1 << 23) | dane[3] | (dane[2] << 8) | ((dane[1] & 0b01111111) << 16))
	
#obliczenie liczby: mantysa/(2^(23-wykładnik)) bo w mantysie wartość jest zapisana jako 1.ułamek
#a ja to traktuję jako liczbę całkowitą i dlatego trzeba przesunąc przecinek w lewo, ale z zapisu binarnego o (23-wykładnik) dlatego dzielę przez 2^ a nie 10^
	if znak==0:
		#liczba dodatnia
		return mantysa/(pow(2,23-wykladnik))
	else:
		#liczba ujemna
		return -mantysa/(pow(2,23-wykladnik))
