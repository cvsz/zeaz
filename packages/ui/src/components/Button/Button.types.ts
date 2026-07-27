import type { ButtonHTMLAttributes } from "react"; export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>{variant?:"primary"|"secondary"|"ghost";loading?:boolean;}
