### A.3 Sexo
**Tabela A.3.1 — Contrastes DDD completos: sexo**
<table header-row="true">
	<tr>
		<td>Grupo (família)</td>
		<td>Resultado</td>
		<td>DDD (EP)</td>
		<td>p nominal / BH</td>
		<td>Pré-tendência grupo / DDD</td>
		<td>N estático DDD</td>
		<td>N evento grupo / DDD</td>
		<td>CBOs alvo T/C · suporte</td>
		<td>MDE 80% grupo / DDD</td>
	</tr>
	<tr>
		<td>Homens (A)</td>
		<td>Admissões</td>
		<td>0,0116 (0,0466)</td>
		<td>0,803 / 0,907</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31861</td>
		<td>75/266 · adequate</td>
		<td>0,0765 / 0,1309</td>
	</tr>
	<tr>
		<td>Homens (A)</td>
		<td>Desligamentos</td>
		<td>0,0332 (0,0390)</td>
		<td>0,395 / 0,581</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31870</td>
		<td>75/266 · adequate</td>
		<td>0,0685 / 0,1096</td>
	</tr>
	<tr>
		<td>Homens (A)</td>
		<td>Fluxo bruto</td>
		<td>0,0216 (0,0420)</td>
		<td>0,607 / 0,742</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31870</td>
		<td>75/266 · adequate</td>
		<td>0,0655 / 0,1179</td>
	</tr>
	<tr>
		<td>Homens (A)</td>
		<td>Salário real (log)</td>
		<td>0,0022 (0,0100)</td>
		<td>0,824 / 0,907</td>
		<td>falha / falha</td>
		<td>43292</td>
		<td>15867 / 31285</td>
		<td>75/266 · adequate</td>
		<td>0,0342 / 0,0281</td>
	</tr>
	<tr>
		<td>Homens (A)</td>
		<td>Saldo (asinh)</td>
		<td>0,7989\*\*\* (0,2145)</td>
		<td>\<0,001 / 0,003</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31870</td>
		<td>75/266 · adequate</td>
		<td>0,9649 / 0,6027</td>
	</tr>
	<tr>
		<td>Mulheres (A)</td>
		<td>Admissões</td>
		<td>−0,0116 (0,0466)</td>
		<td>0,803 / 0,907</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15926 / 31861</td>
		<td>75/266 · adequate</td>
		<td>0,1302 / 0,1309</td>
	</tr>
	<tr>
		<td>Mulheres (A)</td>
		<td>Desligamentos</td>
		<td>−0,0332 (0,0390)</td>
		<td>0,395 / 0,581</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31870</td>
		<td>75/266 · adequate</td>
		<td>0,1043 / 0,1096</td>
	</tr>
	<tr>
		<td>Mulheres (A)</td>
		<td>Fluxo bruto</td>
		<td>−0,0216 (0,0420)</td>
		<td>0,607 / 0,742</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31870</td>
		<td>75/266 · adequate</td>
		<td>0,1142 / 0,1179</td>
	</tr>
	<tr>
		<td>Mulheres (A)</td>
		<td>Salário real (log)</td>
		<td>−0,0022 (0,0100)</td>
		<td>0,824 / 0,907</td>
		<td>falha / falha</td>
		<td>43292</td>
		<td>15418 / 31285</td>
		<td>75/266 · adequate</td>
		<td>0,0329 / 0,0281</td>
	</tr>
	<tr>
		<td>Mulheres (A)</td>
		<td>Saldo (asinh)</td>
		<td>−0,7989\*\*\* (0,2145)</td>
		<td>\<0,001 / 0,003</td>
		<td>falha / falha</td>
		<td>44098</td>
		<td>15935 / 31870</td>
		<td>75/266 · adequate</td>
		<td>0,8472 / 0,6027</td>
	</tr>
</table>
> Notas: cada DDD compara o grupo-alvo com seu complemento, preservando p nominal, p BH e famílias A (100 testes) e B (30). N estático DDD vem do modelo estático; N evento discrimina a amostra do diagnóstico dentro do grupo e a do diagnóstico DDD. CBOs T/C referem-se ao suporte do grupo-alvo, não ao número total de clusters do DDD. MDE informa separadamente o mínimo detectável a 80% de poder no grupo e no DDD. Estrelas usam p BH: \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Falha, alerta e diagnóstico indefinido não autorizam interpretação causal. Saldo em asinh não tem leitura percentual. Fonte: ddd_multiplicity_results.csv, ddd_alternative_partitions.csv e seus diagnósticos.
**Tabela A.3.2 — DiDs dentro dos grupos: sexo**
<table header-row="true">
	<tr>
		<td>Grupo</td>
		<td>Resultado</td>
		<td>DiD (EP)</td>
		<td>p nominal / BH</td>
		<td>Pré-tendência grupo</td>
		<td>N</td>
		<td>CBOs T/C · suporte</td>
	</tr>
	<tr>
		<td>Homens</td>
		<td>Admissões</td>
		<td>−0,0779\*\* (0,0272)</td>
		<td>0,004 / 0,019</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Homens</td>
		<td>Desligamentos</td>
		<td>−0,0635\*\* (0,0244)</td>
		<td>0,010 / 0,034</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Homens</td>
		<td>Fluxo bruto</td>
		<td>−0,0710\*\* (0,0233)</td>
		<td>0,003 / 0,011</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Homens</td>
		<td>Salário real (log)</td>
		<td>−0,0501\*\*\* (0,0122)</td>
		<td>\<0,001 / \<0,001</td>
		<td>falha</td>
		<td>15867</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Homens</td>
		<td>Saldo (asinh)</td>
		<td>−0,2451 (0,3434)</td>
		<td>0,476 / 0,582</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Mulheres</td>
		<td>Admissões</td>
		<td>−0,0724 (0,0464)</td>
		<td>0,119 / 0,228</td>
		<td>falha</td>
		<td>15926</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Mulheres</td>
		<td>Desligamentos</td>
		<td>−0,0776\* (0,0371)</td>
		<td>0,037 / 0,095</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Mulheres</td>
		<td>Fluxo bruto</td>
		<td>−0,0744 (0,0407)</td>
		<td>0,068 / 0,158</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Mulheres</td>
		<td>Salário real (log)</td>
		<td>−0,0491\*\*\* (0,0117)</td>
		<td>\<0,001 / \<0,001</td>
		<td>falha</td>
		<td>15418</td>
		<td>75/266 · adequate</td>
	</tr>
	<tr>
		<td>Mulheres</td>
		<td>Saldo (asinh)</td>
		<td>−1,0188\*\*\* (0,3015)</td>
		<td>\<0,001 / 0,004</td>
		<td>falha</td>
		<td>15935</td>
		<td>75/266 · adequate</td>
	</tr>
</table>
> Notas: DiD dentro do próprio grupo, janela balanceada −23 a +23, com referência em novembro de 2022 e erros agrupados por CBO. A família C contém 130 testes e seu ajuste BH foi preservado integralmente. Estas linhas não testam diferenças entre subgrupos. Os DDDs respondem a essa outra pergunta. Fonte: group_did_results.csv. O suporte e o diagnóstico de pré-tendências são parte do resultado.
Homens e mulheres apresentam orientações opostas do mesmo contraste. A rejeição ajustada no saldo é preservada e não deve ser contada como dois achados substantivos. As pré-tendências DDD falham.
**Figura A.3.1 — Admissões: perfis mensais por sexo**
<image src="file-upload://3e0cc8ca-4610-811f-8b1c-00b2e6b7b2ac"></image>
**Figura A.3.2 — Salário real de admissão: perfis mensais por sexo**
<image src="file-upload://3e0cc8ca-4610-8127-9f05-00b22b408fa6"></image>
> Figuras: séries estendidas de −23 a +41, relativas a novembro de 2022; bandas de 95%, linhas horizontais na média dos coeficientes pré e linha vertical pontilhada em +23. Os testes das tabelas usam −23 a +23. A numeração foi atualizada com os mesmos coeficientes, intervalos e convenções; as imagens anteriores estão preservadas na cópia local da V4.
