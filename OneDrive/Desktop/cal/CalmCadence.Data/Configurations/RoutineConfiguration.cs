using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CalmCadence.Data.Configurations;

public class RoutineConfiguration : IEntityTypeConfiguration<Routine>
{
    public void Configure(EntityTypeBuilder<Routine> builder)
    {
        builder.ToTable("Routines");
        builder.HasKey(r => r.Id);

        builder.Property(r => r.Name).IsRequired().HasMaxLength(200);
        builder.Property(r => r.Description).HasMaxLength(1000);
        builder.Property(r => r.StepsJson).IsRequired();
        builder.Property(r => r.ColorHex).HasMaxLength(9);
        builder.Property(r => r.CreatedAt).IsRequired();
        builder.Property(r => r.UpdatedAt);

        builder.HasIndex(r => r.SortOrder);
        builder.HasIndex(r => r.Enabled);
    }
}
