import { AcademyShell } from "@/components/academy/AcademyShell";

export default function AcademyLayout({ children }: { children: React.ReactNode }) {
  return <AcademyShell>{children}</AcademyShell>;
}
