import { unstable_setRequestLocale } from "next-intl/server";
import AcademyClient from "./AcademyClient";

export default function AcademyPage({
  params,
}: {
  params: { locale: string };
}) {
  unstable_setRequestLocale(params.locale);
  return <AcademyClient />;
}
